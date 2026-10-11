#!/usr/bin/env bash
#SBATCH --job-name=hg002-dna-callers-s0
#SBATCH --partition=amd_256M
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:05:00
# S0 only: direct author binaries, version/help, no genomic inputs or calling.
# Functions can be sourced for offline controls without running main.

hg2_die() { printf 'ERROR: %s\n' "$*" >&2; exit 2; }
hg2_uint() { [[ "$1" =~ ^(0|[1-9][0-9]{0,10})$ ]] || hg2_die "invalid byte/second account: $1"; }
hg2_budget() {
  local cpu_left=$1 body_left=$2 external_disk=$3 body_reserve=$4
  hg2_uint "$cpu_left"; hg2_uint "$body_left"; hg2_uint "$external_disk"
  (( cpu_left >= 300 && cpu_left <= 14400 )) || hg2_die 'S0 needs 300 remaining allocated CPU seconds'
  (( body_left >= body_reserve && body_left <= 4294967296 )) || hg2_die 'insufficient remaining S0 software/reference body account'
  # Reserve a 64-MiB new leaf PLUS its later home copy; external includes all others.
  (( external_disk + 134217728 <= 34359738368 )) || hg2_die 'S0 summed 32-GiB disk account would be exceeded'
}
hg2_scheduler() {
  local record=$1
  grep -Eq '(^|[[:space:]])NumCPUs=1([[:space:]]|$)' "$record" &&
    grep -Eq '(^|[[:space:]])NumNodes=1([[:space:]]|$)' "$record" &&
    grep -Eq '(^|[[:space:]])NumTasks=1([[:space:]]|$)' "$record" &&
    grep -Eq '(^|[[:space:]])TimeLimit=00:05:00([[:space:]]|$)' "$record" &&
    grep -Eq '(^|[[:space:]])MinMemory(Node|CPU)=(2G|2048M)([[:space:]]|$)' "$record" ||
    hg2_die 'require exactly one CPU/task/node, 2 GiB and five minutes'
  ! grep -Eqi 'gres/gpu|Gres=gpu|TresPer(Node|Task)=.*gpu' "$record" || hg2_die 'GPU allocation is out of scope'
}
hg2_new_leaf() {
  local leaf=$1 parent=$2 actual_parent
  [[ "$leaf" == "$parent"/hg002_dna_callers_s0_20261010_[0-9][0-9] ]] || hg2_die 'wrong scratch leaf'
  [[ -d "$parent" && -w "$parent" ]] || hg2_die 'scratch parent is not writable'
  actual_parent=$(cd -P -- "$parent" && pwd)
  [[ "$actual_parent" == "$parent" ]] || hg2_die 'scratch parent aliases another path'
  [[ ! -e "$leaf" && ! -L "$leaf" ]] || hg2_die 'refuse an existing leaf, including symlinks'
  mkdir -- "$leaf"  # Atomic exclusive claim, no mkdir -p or retry.
}
hg2_curl_stream_cap() {
  local version=$1
  [[ "$version" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+) ]] || return 1
  (( BASH_REMATCH[1] > 8 || (BASH_REMATCH[1] == 8 && BASH_REMATCH[2] >= 4) ))
}
hg2_seconds() {
  local requested=$1 left=$(( HG2_DEADLINE - SECONDS ))
  (( left > 0 )) || hg2_die '270-second script deadline reached'
  (( requested <= left )) && printf '%s\n' "$requested" || printf '%s\n' "$left"
}
hg2_verify_asset() {
  local asset_file=$1 expected_bytes=$2 expected_sha=$3 actual_bytes actual_sha
  [[ -f "$asset_file" && ! -L "$asset_file" ]] || hg2_die 'asset is not a regular non-symlink file'
  actual_bytes=$(wc -c < "$asset_file" | tr -d '[:space:]')
  [[ "$actual_bytes" == "$expected_bytes" ]] || hg2_die "asset length mismatch: $actual_bytes != $expected_bytes"
  actual_sha=$(sha256sum "$asset_file" | awk '{print $1}')
  [[ "$expected_sha" == NULL || "$actual_sha" == "$expected_sha" ]] || hg2_die 'asset digest mismatch'
  printf '%s\n' "$actual_sha"
}
hg2_probe() {
  local label=$1 seconds=$2 rc=0
  shift 2
  printf '%q ' "$@" > "$HG2_OUT/logs/$label.command.txt"
  printf '\n' >> "$HG2_OUT/logs/$label.command.txt"
  # Linux Bash -f units are KiB. Logs are capped, never silently truncated.
  (ulimit -f 64; timeout --signal=TERM --kill-after=2s "$(hg2_seconds "$seconds")s" "$@") \
    > "$HG2_OUT/logs/$label.log" 2>&1 || rc=$?
  printf '%s\n' "$rc" > "$HG2_OUT/logs/$label.exit.txt"
  HG2_LAST_RC=$rc
}
hg2_leaf_size() {
  local bytes
  bytes=$(du -sb -- "$HG2_OUT" | awk '{print $1}')
  printf '%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$bytes" >> "$HG2_OUT/disk-samples.tsv"
  (( bytes < 67108864 )) || hg2_die 'new S0 leaf reached its 64-MiB reservation'
}
hg2_fetch() {
  local asset_name=$1 version=$2 bytes=$3 author_sha=$4 commit=$5 asset_id=$6
  local url="https://github.com/PacificBiosciences/$asset_name/releases/download/v$version/$asset_name"
  local partial="$HG2_OUT/assets/$asset_name.partial" asset="$HG2_OUT/assets/$asset_name"
  local verify_sha=$author_sha observed_sha method rc=0
  if [[ -n "$HG2_CACHE" ]]; then
    method=VERIFIED_RETAINED_COPY
    [[ "$asset_name" != pbsv ]] || verify_sha=$HG2_PBSV_OBSERVED
    # Check explicit retained files before copying; no cache inventory or fallback.
    hg2_verify_asset "$HG2_CACHE/$asset_name" "$bytes" "$verify_sha" > "$HG2_OUT/$asset_name.cache-verified.sha256"
    cp -p -- "$HG2_CACHE/$asset_name" "$partial"
    printf '0\n' > "$HG2_OUT/logs/$asset_name.download.exit.txt"
    printf 'NO_NETWORK retained source: %s/%s\n' "$HG2_CACHE" "$asset_name" > "$HG2_OUT/logs/$asset_name.download.log"
  else
    method=ONE_HTTPS_ATTEMPT
    # -q first disables curlrc. TLS verification stays on; no netrc/auth/--insecure.
    (ulimit -f 16384; curl -q --fail --location --max-redirs 3 --silent --show-error \
      --proto '=https' --proto-redir '=https' --retry 0 --connect-timeout 20 \
      --max-time "$(hg2_seconds 120)" --max-filesize "$bytes" --output "$partial" \
      --write-out 'http_code=%{http_code}\nsize_download=%{size_download}\nssl_verify_result=%{ssl_verify_result}\ntime_total=%{time_total}\nnum_redirects=%{num_redirects}\n' \
      "$url") > "$HG2_OUT/logs/$asset_name.download.metrics.txt" \
      2> "$HG2_OUT/logs/$asset_name.download.log" || rc=$?
    printf '%s\n' "$rc" > "$HG2_OUT/logs/$asset_name.download.exit.txt"
    (( rc == 0 )) || hg2_die "$asset_name download failed; preserve partial, no retry"
    grep -qx 'http_code=200' "$HG2_OUT/logs/$asset_name.download.metrics.txt" || hg2_die 'unexpected final HTTP status'
  fi
  observed_sha=$(hg2_verify_asset "$partial" "$bytes" "$verify_sha")
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$asset_name" "$version" "$asset_id" "$bytes" "$author_sha" "$observed_sha" "$commit" "$method" "$url" >> "$HG2_OUT/assets.tsv"
  ln -- "$partial" "$asset"; unlink -- "$partial"  # Exclusive publication only after checks.
  cp -p -- "$asset" "$HG2_OUT/bin/$asset_name"
  chmod 700 "$HG2_OUT/bin/$asset_name"  # Absolute path cannot be parsed as an option.
  hg2_leaf_size
}
hg2_license() {
  local asset_name=$1 years=$2
  {
    printf 'Copyright (c) %s, Pacific Biosciences of California, Inc.\n\n' "$years"
    cat <<'LICENSE'
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted (subject to the limitations in the
disclaimer below) provided that the following conditions are met:

 * Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.

 * Redistributions in binary form must reproduce the above
   copyright notice, this list of conditions and the following
   disclaimer in the documentation and/or other materials provided
   with the distribution.

 * Neither the name of Pacific Biosciences nor the names of its
   contributors may be used to endorse or promote products derived
   from this software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE
GRANTED BY THIS LICENSE. THIS SOFTWARE IS PROVIDED BY PACIFIC
BIOSCIENCES AND ITS CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL PACIFIC BIOSCIENCES OR ITS
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
LICENSE
  } > "$HG2_OUT/$asset_name.LICENSE"
}
hg2_finish() {
  local rc=$?
  trap - EXIT INT TERM
  set +e
  printf 'exit_code=%s\n' "$rc" > "$HG2_OUT/exit-status.txt"
  if (( rc == 0 )); then printf 'CLI_CONTROLS_COMPLETE\n'; else printf 'INCOMPLETE\n'; fi > "$HG2_OUT/status.txt"
  printf 'finished_utc=%s\nscript_elapsed_seconds=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$SECONDS"
  # Close the synchronous log before hashing it; include final exit/status and failures.
  exec 1>&3 2>&4 3>&- 4>&-
  if ! (cd "$HG2_OUT" && find . -type f ! -name artifact-sha256sums.txt ! -name artifact-sha256sums.partial -print0 | \
    LC_ALL=C sort -z | xargs -0 sha256sum > artifact-sha256sums.partial && \
    ln artifact-sha256sums.partial artifact-sha256sums.txt && unlink artifact-sha256sums.partial); then
    rc=2
    printf 'INCOMPLETE\n' > "$HG2_OUT/status.txt"
    printf 'exit_code=2\n' > "$HG2_OUT/exit-status.txt"
    printf 'Artifact hash publication failed; partial manifest is not authoritative.\n' >&2
  fi
  printf 'packet=%s exit_code=%s; no caller was launched\n' "$HG2_OUT" "$rc"
  exit "$rc"
}
hg2_main() {
  set -Eeuo pipefail
  umask 077
  ulimit -c 0
  local parent=/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments
  local cpu_left= body_left= external_disk= body_reserve=134217728 tool tool_path script_path script_sha native_bad=0
  HG2_OUT="$parent/hg002_dna_callers_s0_20261010_01"
  HG2_CACHE=; HG2_PBSV_OBSERVED=; HG2_DEADLINE=$(( SECONDS + 270 )); HG2_LAST_RC=0
  while (( $# )); do
    (( $# >= 2 )) || hg2_die 'options need values'
    case "$1" in
      --output) HG2_OUT=$2 ;;
      --remaining-s0-cpu-seconds) cpu_left=$2 ;;
      --remaining-s0-body-bytes) body_left=$2 ;;
      --external-s0-reserved-bytes) external_disk=$2 ;;
      --asset-cache) HG2_CACHE=$2 ;;
      --pbsv-observed-sha256) HG2_PBSV_OBSERVED=$2 ;;
      *) hg2_die "unknown option: $1" ;;
    esac
    shift 2
  done
  if [[ -n "$HG2_CACHE" ]]; then
    [[ "$HG2_CACHE" == /* && -d "$HG2_CACHE" && ! -L "$HG2_CACHE" && "$HG2_PBSV_OBSERVED" =~ ^[0-9a-f]{64}$ ]] ||
      hg2_die 'offline mode needs an absolute retained asset directory and independently recorded pbsv observed SHA256'
    body_reserve=0
  else
    [[ -z "$HG2_PBSV_OBSERVED" ]] || hg2_die 'observed cache digest is only valid with --asset-cache'
  fi
  hg2_budget "$cpu_left" "$body_left" "$external_disk" "$body_reserve"
  for tool in mkdir grep awk tr wc sha256sum cp chmod ln unlink du df date find sort xargs timeout scontrol uname file readelf ldd readlink cat; do
    command -v "$tool" >/dev/null || hg2_die "missing prerequisite: $tool (no install attempted)"
  done
  [[ -n "$HG2_CACHE" ]] || command -v curl >/dev/null || hg2_die 'online mode requires curl'
  hg2_new_leaf "$HG2_OUT" "$parent"
  exec 3>&1 4>&2
  exec > "$HG2_OUT/setup.log" 2>&1
  trap hg2_finish EXIT
  trap 'exit 143' TERM
  trap 'exit 130' INT
  mkdir "$HG2_OUT/assets" "$HG2_OUT/bin" "$HG2_OUT/logs"
  printf 'started_utc=%s\nbody_reservation_bytes=%s\nremaining_s0_cpu_seconds=%s\nremaining_s0_body_bytes=%s\nexternal_s0_reserved_bytes=%s\nnew_leaf_and_home_reservation_bytes=134217728\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$body_reserve" "$cpu_left" "$body_left" "$external_disk" > "$HG2_OUT/budget.txt"
  script_path=$(readlink -f -- "${BASH_SOURCE[0]}")
  cp -- "$script_path" "$HG2_OUT/setup-script.sh"
  script_sha=$(sha256sum "$HG2_OUT/setup-script.sh" | awk '{print $1}')
  printf '%s\n' "$script_sha" > "$HG2_OUT/setup-script.sha256"
  (( $(df -Pk -- "$parent" | awk 'END {print $4}') >= 131072 )) || hg2_die 'need 128 MiB physical scratch free, independently of the summed S0 account'
  [[ -z "$HG2_CACHE" || "$(readlink -f -- "$HG2_CACHE")" == "$HG2_CACHE" ]] || hg2_die 'cache path aliases another location'
  [[ "${SLURM_JOB_ID:-}" =~ ^[0-9]+$ && "${SLURM_CPUS_PER_TASK:-}" == 1 ]] || hg2_die 'must run in the one-CPU Slurm allocation'
  hg2_probe slurm-allocation 8 scontrol show job "$SLURM_JOB_ID" --oneliner
  (( HG2_LAST_RC == 0 )) || hg2_die 'cannot attest Slurm limits'
  hg2_scheduler "$HG2_OUT/logs/slurm-allocation.log"
  [[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 ]] || hg2_die 'requires Linux x86_64; binary format still needs qualification'
  grep -qw sse4_1 /proc/cpuinfo || hg2_die 'pbsv requires SSE4.1'
  uname -a > "$HG2_OUT/platform.txt"
  for tool in bash curl timeout scontrol sha256sum file readelf ldd cp; do
    if tool_path=$(command -v "$tool"); then printf '%s\t%s\n' "$tool" "$(readlink -f -- "$tool_path")"; fi
  done > "$HG2_OUT/toolpaths.tsv"
  if [[ -z "$HG2_CACHE" ]]; then
    hg2_probe curl-version 8 curl -q --version
    (( HG2_LAST_RC == 0 )) && hg2_curl_stream_cap "$(awk 'NR==1 {print $2}' "$HG2_OUT/logs/curl-version.log")" ||
      hg2_die 'online mode needs curl >=8.4.0 for unknown-length stream limits; use a separately verified cache, not an automatic retry'
  fi
  printf 'tool\tversion\tasset_id\texact_bytes\tauthor_api_sha256\tobserved_sha256\tdocumentation_tag_commit\tmethod\tsource_url\n' > "$HG2_OUT/assets.tsv"
  printf 'tool\treadme_blob_sha\tlicense_blob_sha\n' > "$HG2_OUT/documentation.tsv"
  printf 'pbmm2\ta1b484e21dfc5722bbb3063914454e4c7a666069\t2bcaa371a4e7ef8083189468f18da18eeb502d0f\npbsv\t93dec00c8ac80d457d0acda55a47ea22cff0f044\t736c7ba1f074d9882dc6e19403ce82cdfe16a79b\n' >> "$HG2_OUT/documentation.tsv"
  hg2_license pbmm2 2017-2018; hg2_license pbsv 2018
  hg2_fetch pbmm2 26.2.0 5962520 f8a583d27a6232706c8ffe31dab3e52815455032517e9c1399940d4a3ea612bc c0ebc3301a6978c453bc87ecc482eb0de40b9367 462459777
  hg2_fetch pbsv 2.11.0 9756600 NULL a99dfd9b8dfe91f9c2ad2024f2ba02ea157923e5 232792914
  for tool in pbmm2 pbsv; do
    hg2_probe "$tool.file" 8 file "$HG2_OUT/bin/$tool"
    (( HG2_LAST_RC == 0 )) && grep -Eq 'ELF 64-bit.*x86-64' "$HG2_OUT/logs/$tool.file.log" || hg2_die "$tool is not an ELF64 x86-64 binary"
    hg2_probe "$tool.elf-header" 8 readelf -h "$HG2_OUT/bin/$tool"
    (( HG2_LAST_RC == 0 )) || hg2_die 'ELF header qualification failed'
    hg2_probe "$tool.elf-dynamic" 8 readelf -d "$HG2_OUT/bin/$tool"
    (( HG2_LAST_RC == 0 )) || native_bad=1
    hg2_probe "$tool.ldd" 8 ldd "$HG2_OUT/bin/$tool"
    if (( HG2_LAST_RC != 0 )) && ! grep -Eqi 'not a dynamic executable|statically linked' "$HG2_OUT/logs/$tool.ldd.log"; then native_bad=1; fi
    ! grep -q 'not found' "$HG2_OUT/logs/$tool.ldd.log" || native_bad=1
    hg2_probe "$tool.version" 8 "$HG2_OUT/bin/$tool" --version
    (( HG2_LAST_RC == 0 )) || native_bad=1
    hg2_probe "$tool.root-help" 8 "$HG2_OUT/bin/$tool" --help
    (( HG2_LAST_RC == 0 )) || native_bad=1
  done
  grep -Eq '(^|[^0-9])26\.2\.0([^0-9.]|$)' "$HG2_OUT/logs/pbmm2.version.log" || native_bad=1
  grep -Eq '(^|[^0-9])2\.11\.0([^0-9.]|$)' "$HG2_OUT/logs/pbsv.version.log" || native_bad=1
  hg2_probe pbmm2.align-help 8 "$HG2_OUT/bin/pbmm2" align --help
  (( HG2_LAST_RC == 0 )) || native_bad=1
  hg2_probe pbsv.discover-help 8 "$HG2_OUT/bin/pbsv" discover --help
  (( HG2_LAST_RC == 0 )) || native_bad=1
  hg2_probe pbsv.call-help 8 "$HG2_OUT/bin/pbsv" call --help
  (( HG2_LAST_RC == 0 )) || native_bad=1
  for tool in pbmm2.root pbsv.root pbmm2.align pbsv.discover pbsv.call; do
    grep -Eqi 'usage|options' "$HG2_OUT/logs/$tool-help.log" || native_bad=1
  done
  hg2_verify_asset "$HG2_OUT/bin/pbmm2" 5962520 f8a583d27a6232706c8ffe31dab3e52815455032517e9c1399940d4a3ea612bc > "$HG2_OUT/pbmm2.binary.sha256"
  hg2_verify_asset "$HG2_OUT/bin/pbsv" 9756600 "$(awk -F '\t' '$1=="pbsv" {print $6}' "$HG2_OUT/assets.tsv")" > "$HG2_OUT/pbsv.binary.sha256"
  [[ "$(sha256sum "$script_path" | awk '{print $1}')" == "$script_sha" ]] || hg2_die 'setup source changed during execution'
  hg2_leaf_size
  (( native_bad == 0 )) || hg2_die 'one or more native controls failed; inspect retained logs, no automatic repair'
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then hg2_main "$@"; fi
