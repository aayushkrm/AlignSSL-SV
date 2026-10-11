#!/usr/bin/env bash
# Small official SOFTWARE assets only. Never execute these Linux binaries here.
set -Eeuo pipefail
umask 077
ulimit -c 0
parent=/Users/akm/aayushkrm-AlignSSL/runs
out="$parent/hg002-caller-assets-20261011-01"
[[ $# == 0 && -d "$parent" && ! -e "$out" && ! -L "$out" ]]
[[ "$(cd -P "$parent" && pwd)" == "$parent" ]]
version=$(/usr/bin/curl -q --version | awk 'NR==1 {print $2}')
[[ "$version" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+) ]]
(( BASH_REMATCH[1] > 8 || (BASH_REMATCH[1] == 8 && BASH_REMATCH[2] >= 4) ))
(( $(df -Pk "$parent" | awk 'END {print $4}') > 10485760 ))
mkdir "$out"
finish() { local rc=$?; trap - EXIT; printf 'exit_code=%s\n' "$rc" > "$out/exit-status.txt"; exit "$rc"; }
trap finish EXIT
mkdir "$out/assets"
printf 'started_utc=%s\ncurl_version=%s\nsoftware_body_reservation_bytes=134217728\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$version" > "$out/execution.txt"
printf 'tool\tversion\texact_bytes\tauthor_api_sha256\tobserved_sha256\tsource_url\n' > "$out/assets.tsv"
fetch() {
  local tool=$1 tag=$2 bytes=$3 expected=$4 rc=0 sha
  local url="https://github.com/PacificBiosciences/$tool/releases/download/$tag/$tool"
  # curl >=8.4 enforces max-filesize on unknown-length streams too. One attempt.
  /usr/bin/curl -q --fail --location --max-redirs 3 --silent --show-error \
    --proto '=https' --proto-redir '=https' --retry 0 --connect-timeout 20 \
    --max-time 120 --max-filesize "$bytes" --output "$out/assets/$tool.partial" \
    --write-out 'http_code=%{http_code}\nsize_download=%{size_download}\nssl_verify_result=%{ssl_verify_result}\ntime_total=%{time_total}\nnum_redirects=%{num_redirects}\n' \
    "$url" > "$out/$tool.download.metrics.txt" 2> "$out/$tool.download.stderr.txt" || rc=$?
  printf '%s\n' "$rc" > "$out/$tool.download.exit.txt"
  (( rc == 0 ))
  grep -qx 'http_code=200' "$out/$tool.download.metrics.txt"
  grep -qx 'ssl_verify_result=0' "$out/$tool.download.metrics.txt"
  [[ "$(wc -c < "$out/assets/$tool.partial" | tr -d '[:space:]')" == "$bytes" ]]
  sha=$(shasum -a 256 "$out/assets/$tool.partial" | awk '{print $1}')
  [[ "$expected" == NULL || "$sha" == "$expected" ]]
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$tool" "$tag" "$bytes" "$expected" "$sha" "$url" >> "$out/assets.tsv"
  ln "$out/assets/$tool.partial" "$out/assets/$tool"
  unlink "$out/assets/$tool.partial"
}
fetch pbmm2 v26.2.0 5962520 f8a583d27a6232706c8ffe31dab3e52815455032517e9c1399940d4a3ea612bc
fetch pbsv v2.11.0 9756600 NULL
printf 'completed_utc=%s\nselected_payload_bytes=15719120\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$out/execution.txt"
# pbsv's observed digest is not an author checksum. No caller is run.
