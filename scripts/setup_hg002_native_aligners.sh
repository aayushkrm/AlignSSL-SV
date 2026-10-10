#!/usr/bin/env bash
# S0 software setup only. No reference or genomic input is read.
set -Eeuo pipefail
umask 077

scratch=/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922
parent="$scratch/experiments"
out="$parent/hg002_native_aligners_s0_20261010_02"
source_cache=/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/hg002_native_aligners_s0_20261010_01/source_archives
[[ -d "$parent" && -w "$parent" ]] || { echo "Scratch experiment parent is not writable: $parent" >&2; exit 2; }
[[ ! -e "$out" && ! -L "$out" ]] || { echo "Refusing existing output: $out" >&2; exit 2; }
command -v tee >/dev/null || { echo "Missing required command: tee" >&2; exit 2; }
mkdir "$out"

finish() {
  local rc=$?
  trap - EXIT
  printf 'exit_code=%s\n' "$rc" > "$out/exit-status.txt" 2>/dev/null || true
  exit "$rc"
}
trap finish EXIT
exec > >(tee -a "$out/setup.log") 2>&1

die() { printf 'ERROR: %s\n' "$*" >&2; exit 2; }
[[ -n "${SLURM_JOB_ID:-}" ]] || die "run inside the bounded Slurm allocation"
[[ "${SLURM_CPUS_PER_TASK:-}" == 4 ]] || die "requires one 4-CPU task"
nodes=${SLURM_JOB_NUM_NODES:-${SLURM_NNODES:-}}
[[ "$nodes" == 1 ]] || die "requires exactly one node"
[[ "${SLURM_GPUS_ON_NODE:-0}" == 0 ]] || die "GPU allocation is out of scope"
for tool in cp tar bzip2 sha256sum make cc awk sort grep tee sed wc tr date df uname; do
  command -v "$tool" >/dev/null || die "missing required command: $tool"
done

mkdir "$out/source_archives" "$out/source" "$out/bin" "$out/tmp"
export TMPDIR="$out/tmp"
free_kb=$(df -Pk "$parent" | awk 'END {print $4}')
[[ "$free_kb" =~ ^[0-9]+$ ]] && (( free_kb >= 1048576 )) || die "need at least 1 GiB free in scratch"

printf 'started_utc=%s\njob_id=%s\ncpus_per_task=%s\nnodes=%s\ngpus_on_node=%s\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$SLURM_JOB_ID" "$SLURM_CPUS_PER_TASK" "$nodes" "${SLURM_GPUS_ON_NODE:-0}"
script_sha=$(sha256sum "$0" | awk '{print $1}')
printf 'script_sha256=%s\n' "$script_sha"
printf '%s\n' "$script_sha" > "$out/setup-script.sha256"
uname -a
cc --version | sed -n '1p'
make --version | sed -n '1p'
printf 'tool\tversion\ttag_commit\tarchive_bytes\tsource_sha256\tsource_url\n' > "$out/source-manifest.tsv"

copy_source() {
  local tool=$1 version=$2 commit=$3 bytes=$4 digest=$5 url=$6
  local archive="$out/source_archives/$tool.tar.bz2"
  # No redownload: attempt 01 already verified these exact author assets.
  cp -p "$source_cache/$tool.tar.bz2" "$archive"
  local actual_bytes actual_sha
  actual_bytes=$(wc -c < "$archive" | tr -d '[:space:]')
  [[ "$actual_bytes" == "$bytes" ]] || die "$tool source size mismatch: $actual_bytes != $bytes"
  printf '%s  %s\n' "$digest" "$archive" | sha256sum --check --status || die "$tool source SHA256 mismatch"
  actual_sha=$(sha256sum "$archive" | awk '{print $1}')
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$tool" "$version" "$commit" "$actual_bytes" "$actual_sha" "$url" >> "$out/source-manifest.tsv"
}

build_source() {
  local tool=$1 archive=$2
  local dest="$out/source/$tool" listing="$out/$tool.tar-members.txt" roots root src
  mkdir "$dest"
  tar -tjf "$archive" > "$listing"
  if grep -Eq '(^/|(^|/)\.\.(/|$))' "$listing"; then die "$tool archive has an unsafe path"; fi
  roots=$(awk -F/ 'NF {print $1}' "$listing" | sort -u)
  [[ -n "$roots" && "$roots" != *$'\n'* ]] || die "$tool archive must have one top-level directory"
  root=$roots
  tar -xjf "$archive" -C "$dest"
  src="$dest/$root"
  [[ -f "$src/Makefile" ]] || die "$tool source Makefile is missing"
  # An inherited CC points to an absent NVIDIA compiler; use the checked cc.
  make -C "$src" -j4 CC=cc 2>&1 | tee "$out/$tool.make.log"
  [[ -x "$src/$tool" ]] || die "$tool build did not produce an executable"
  cp -p "$src/$tool" "$out/bin/$tool"
}

copy_source minimap2 2.31 3c28777e7e2dcc90f825de1b9f17a89cca7d4452 187931 c1351de6319c123369c2f4f37ba0ccf18c7ace47e2b1c0a35e30056b4a3bd9c9 \
  https://github.com/lh3/minimap2/releases/download/v2.31/minimap2-2.31.tar.bz2
copy_source miniprot 0.18 671db243f964a68bd724af11cd9964d840f29c43 71853 307428a8da5854fa4c2f078ff0ca07756143b28e1598b8247c727ca2b87b15b1 \
  https://github.com/lh3/miniprot/releases/download/v0.18/miniprot-0.18.tar.bz2
build_source minimap2 "$out/source_archives/minimap2.tar.bz2"
build_source miniprot "$out/source_archives/miniprot.tar.bz2"

for tool in minimap2 miniprot; do
  if [[ "$tool" == minimap2 ]]; then expected_version=2.31; else expected_version=0.18; fi
  "$out/bin/$tool" --version > "$out/$tool.version.txt" 2>&1
  grep -Fq "$expected_version" "$out/$tool.version.txt" || die "$tool version output does not match the pin"
  help_rc=0
  "$out/bin/$tool" -h > "$out/$tool.help.txt" 2>&1 || help_rc=$?
  [[ -s "$out/$tool.help.txt" ]] && grep -qi "$tool" "$out/$tool.help.txt" && \
    grep -Eiq 'usage|options' "$out/$tool.help.txt" || die "$tool help output is missing"
  printf 'exit_code=%s\n' "$help_rc" > "$out/$tool.help-exit.txt"
done

(
  cd "$out"
  sha256sum source_archives/*.tar.bz2 bin/minimap2 bin/miniprot setup-script.sha256 source-manifest.tsv \
    minimap2.version.txt miniprot.version.txt minimap2.help.txt miniprot.help.txt \
    minimap2.help-exit.txt miniprot.help-exit.txt minimap2.make.log miniprot.make.log > artifact-sha256sums.txt
  sha256sum --check artifact-sha256sums.txt
)
printf 'completed_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
# Keep source archives, extracted trees, logs, binaries and hash records.
# Back up the complete output through writable login-side I/O before scratch expiry.
