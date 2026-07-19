#!/bin/bash
# pfetch_bam.sh — parallel chunked BAM downloader with full-scan integrity gate.
# Usage: pfetch_bam.sh <SAMPLE> <FNAME> <DESTDIR> <NPAR>
# Downloads via N concurrent curl --range chunks, verifies each chunk length,
# concatenates in order, fetches .bai, then gates on samtools view -c.
# Auto-retries the whole file up to 3 times on integrity failure (fresh, no --continue).
#
# 2026-07-18 FINDING: the first real production use of this script (3 samples
# launched simultaneously -> 48 concurrent Range requests against the same EBI
# host) failed the integrity gate 2-for-2 (NA20845, NA19017), both times with
# the identical signature: assembled byte count matched Content-Length exactly,
# but samtools failed with a truncated BGZF block partway through (e.g. "506 of
# 1175 bytes"). Every download that used the OLD single-stream method (no
# concurrent Range requests) completed cleanly. This points to Range-response
# corruption/confusion under concurrent load against the same URL (a known
# failure class for reverse-proxy/CDN caches that don't vary cache keys by
# Range), not a boundary-arithmetic bug in this script (ranges are computed as
# an exact, non-overlapping, gap-free partition of [0, TOTAL)).
# FIX: (1) a cross-job mkdir-based mutex so at most one pfetch invocation is actively
# downloading chunks cluster-wide at a time (serializes concurrent-job Range
# contention against the shared EBI host); (2) default NPAR lowered 16->8 to
# reduce per-job load. This does not change already-running jobs (bash does not
# safely hot-reload a running script's loop body), only future launches.
set -u
SAMPLE="$1"; FNAME="$2"; DEST="$3"; NPAR="${4:-8}"
URL="https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/data/${SAMPLE}/high_coverage_alignment/${FNAME}"
BAI_URL="${URL}.bai"
BAM="${DEST}/${FNAME}"
CHUNKDIR="${DEST}/.chunks_${SAMPLE}"
LOCKDIR="${DEST}/.pfetch_download.lock"

echo "PFETCH start sample=${SAMPLE} url=${URL} npar=${NPAR} $(date)"

# Cross-job mutex: wait until no other pfetch invocation is in its download
# phase, then hold the lock for the duration of THIS download phase. Uses a
# mkdir-based lock (atomic on shared filesystems, no flock-on-NFS pitfalls).
acquire_lock() {
  local waited=0
  while ! mkdir "$LOCKDIR" 2>/dev/null; do
    if [ "$waited" -eq 0 ] || [ $(( waited % 300 )) -eq 0 ]; then
      echo "PFETCH ${SAMPLE} waiting for download mutex (held by $(cat "$LOCKDIR/owner" 2>/dev/null || echo unknown)), waited=${waited}s $(date)"
    fi
    sleep 5
    waited=$(( waited + 5 ))
  done
  echo "$SAMPLE.$$" > "$LOCKDIR/owner" 2>/dev/null || true
}
release_lock() {
  rm -rf "$LOCKDIR" 2>/dev/null || true
}
trap release_lock EXIT

# Discover total size via HTTP HEAD (Content-Length)
get_size() {
  curl -sI "$URL" | tr -d '\r' | awk 'tolower($1)=="content-length:"{print $2}' | tail -1
}
TOTAL=$(get_size)
if ! [[ "$TOTAL" =~ ^[0-9]+$ ]] || [ "$TOTAL" -le 0 ]; then
  echo "PFETCH_FAIL ${SAMPLE}: could not get Content-Length (got '$TOTAL')"; exit 1
fi
echo "PFETCH ${SAMPLE} total_bytes=${TOTAL}"

for attempt in 1 2 3; do
  echo "=== ATTEMPT ${attempt} for ${SAMPLE} $(date) ==="
  rm -f "$BAM" "${BAM}.bai"
  rm -rf "$CHUNKDIR"; mkdir -p "$CHUNKDIR"

  # Compute chunk boundaries
  CHUNK=$(( (TOTAL + NPAR - 1) / NPAR ))
  pids=()
  ranges=()
  idx=0
  off=0
  while [ "$off" -lt "$TOTAL" ]; do
    end=$(( off + CHUNK - 1 ))
    if [ "$end" -ge "$TOTAL" ]; then end=$(( TOTAL - 1 )); fi
    ranges[$idx]="${off}-${end}"
    idx=$(( idx + 1 ))
    off=$(( end + 1 ))
  done
  NCHUNK=${#ranges[@]}
  echo "PFETCH ${SAMPLE} nchunks=${NCHUNK} chunk_bytes=${CHUNK}"

  # Serialize the concurrent-Range phase across jobs cluster-wide (see header
  # note: concurrent multi-job Range requests against the same host/URL
  # produced corrupted BGZF blocks in production; single-job-at-a-time did not).
  acquire_lock
  echo "PFETCH ${SAMPLE} acquired download mutex $(date)"

  # Launch concurrent range downloads
  for i in $(seq 0 $((NCHUNK-1))); do
    rng="${ranges[$i]}"
    part=$(printf "%s/part_%05d" "$CHUNKDIR" "$i")
    (
      for t in 1 2 3 4 5; do
        curl -s --fail --range "$rng" -o "$part" "$URL" && break
        echo "  chunk $i range $rng retry $t"; sleep 15
      done
    ) &
    pids+=($!)
  done
  # Wait for all, capture failures
  fail=0
  for p in "${pids[@]}"; do wait "$p" || fail=1; done

  release_lock
  echo "PFETCH ${SAMPLE} released download mutex $(date)"

  # Verify each chunk length
  badlen=0
  for i in $(seq 0 $((NCHUNK-1))); do
    rng="${ranges[$i]}"
    exp=$(( ${rng#*-} - ${rng%-*} + 1 ))
    part=$(printf "%s/part_%05d" "$CHUNKDIR" "$i")
    got=$(stat -c %s "$part" 2>/dev/null || echo 0)
    if [ "$got" != "$exp" ]; then echo "  BADLEN chunk $i exp=$exp got=$got"; badlen=1; fi
  done
  if [ "$fail" != "0" ] || [ "$badlen" != "0" ]; then
    echo "PFETCH ${SAMPLE} attempt ${attempt}: chunk download/length failure, retrying"
    continue
  fi

  # Concatenate in order
  : > "$BAM"
  for i in $(seq 0 $((NCHUNK-1))); do
    part=$(printf "%s/part_%05d" "$CHUNKDIR" "$i")
    cat "$part" >> "$BAM" || { echo "cat fail $i"; break; }
  done
  ASM=$(stat -c %s "$BAM" 2>/dev/null || echo 0)
  echo "PFETCH ${SAMPLE} assembled_bytes=${ASM} expected=${TOTAL}"
  if [ "$ASM" != "$TOTAL" ]; then
    echo "PFETCH ${SAMPLE} attempt ${attempt}: assembled size mismatch, retrying"; continue
  fi
  rm -rf "$CHUNKDIR"

  # Integrity gate: full BGZF scan
  echo "PFETCH ${SAMPLE} running samtools view -c (full scan) $(date)"
  SCAN=$(samtools view -c "$BAM" 2>"${DEST}/.scan_${SAMPLE}.err")
  SCAN_EXIT=$?
  if [ "$SCAN_EXIT" == "0" ]; then
    echo "PFETCH ${SAMPLE} SCAN_OK reads=${SCAN}"
    md5sum "$BAM" > "${BAM}.ourmd5"
    # Fetch .bai
    for t in 1 2 3 4 5; do
      curl -s --fail -o "${BAM}.bai" "$BAI_URL" && break
      echo "  bai retry $t"; sleep 15
    done
    echo "DONE_${SAMPLE}_SUCCESS bytes=${TOTAL} reads=${SCAN}"
    exit 0
  else
    echo "PFETCH ${SAMPLE} INTEGRITY_FAIL scan_exit=${SCAN_EXIT}"
    cat "${DEST}/.scan_${SAMPLE}.err"
    echo "retrying from scratch"
  fi
done
echo "PFETCH_FAIL ${SAMPLE}: all 3 attempts failed"
exit 1
