"""Frozen parental SVA CIGAR census; compatible evidence, not child-allele truth."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path

CHROM = "chr3"
ANCHOR = 71589909  # query neighborhood, not an asserted workbook convention
BUFFER = (71539909, 71643317)
CORE = (71579909, 71603317)
INS_LENGTH = (math.ceil(3407 * .8), math.floor(3407 * 1.2))


def aligned_bases(cigar, start, low, high):
    """Count M/= /X in one reference interval, excluding deletions/skips."""
    count = 0
    for op, length in cigar:
        if op in (0, 7, 8):
            count += max(0, min(start + length, high) - max(start, low))
        if op in (0, 2, 3, 7, 8):
            start += length
    return count


def cigar_events(cigar, start, sequence):
    query = 0
    events = []
    for op, length in cigar:
        if op == 1 and length >= 50:
            inserted = sequence[query:query + length] if sequence else None
            if inserted is not None and len(inserted) != length:
                raise ValueError("Incomplete insertion sequence")
            events.append({"type": "INS", "position0": start, "length": length,
                           "sequence": inserted})
        elif op in (2, 3) and length >= 50:
            events.append({"type": "DEL" if op == 2 else "SKIP",
                           "position0": start, "length": length})
        if op in (0, 1, 4, 7, 8):
            query += length
        if op in (0, 2, 3, 7, 8):
            start += length
    return events


def classify(cigar, start, sequence):
    events = cigar_events(cigar, start, sequence)
    left = aligned_bases(cigar, start, ANCHOR - 1000, ANCHOR)
    right = aligned_bases(cigar, start, ANCHOR, ANCHOR + 1000)
    compatible = [e for e in events if e["type"] == "INS"
                  and abs(e["position0"] - ANCHOR) <= 500
                  and INS_LENGTH[0] <= e["length"] <= INS_LENGTH[1]]
    near = [e for e in events if
            e["position0"] <= ANCHOR + 500 and
            e["position0"] + (e["length"] if e["type"] != "INS" else 0) >= ANCHOR - 500]
    if min(left, right) < 500:
        category = "insufficient_aligned_flanks"
    elif compatible:
        category = "compatible_insertion" if len(compatible) == 1 else "multiple_compatible_insertions"
    elif near:
        category = "other_structural_cigar"
    else:
        category = "reference_compatible_cigar"
    return category, left, right, events


def sa_outside_buffer(sa):
    result = []
    for entry in sa.split(";"):
        if not entry:
            continue
        fields = entry.split(",")
        if len(fields) != 6:
            raise ValueError("Malformed SA tag")
        pos = int(fields[1]) - 1
        if fields[0] != CHROM or not BUFFER[0] <= pos < BUFFER[1]:
            result.append(entry)
    return result


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    import pysam
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bam", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False, parents=True)
    records = collections.defaultdict(list)
    flags = collections.Counter()
    with pysam.AlignmentFile(str(args.bam), "rb", require_index=True) as bam:
        if bam.get_reference_length(CHROM) != 201105948:
            raise ValueError("Unexpected chr3 dictionary")
        groups = bam.header.to_dict().get("RG", [])
        if not groups or {g.get("SM") for g in groups} != {"NA12878"}:
            raise ValueError("Unexpected sample identity")
        for read in bam.fetch(CHROM, ANCHOR - 1000, ANCHOR + 1001):
            if read.is_unmapped or read.is_secondary or read.is_supplementary or read.is_qcfail or read.is_duplicate:
                flags["excluded_flags"] += 1
                continue
            if read.mapping_quality < 20:
                flags["mapq_below20"] += 1
                continue
            if not read.cigartuples:
                raise ValueError("Mapped read without CIGAR")
            category, left, right, events = classify(read.cigartuples, read.reference_start, read.query_sequence)
            records[read.query_name].append({"name": read.query_name, "category": category,
                "start0": read.reference_start, "end0": read.reference_end,
                "cigar": read.cigarstring, "mapq": read.mapping_quality,
                "rg": read.get_tag("RG") if read.has_tag("RG") else None,
                "hp": read.get_tag("HP") if read.has_tag("HP") else None,
                "left_aligned": left, "right_aligned": right, "events": events,
                "sa_outside_buffer": sa_outside_buffer(read.get_tag("SA")) if read.has_tag("SA") else []})
    counts = collections.Counter()
    output_records = []
    with (args.output / "insertion_sequences.fasta").open("x") as fasta:
        for name, observations in sorted(records.items()):
            category = observations[0]["category"] if len(observations) == 1 else "duplicate_primary_name"
            counts[category] += 1
            for obs in observations:
                obs["molecule_category"] = category
                for event in obs["events"]:
                    sequence = event.pop("sequence", None)
                    if sequence is not None:
                        event["sequence_sha256"] = hashlib.sha256(sequence.encode()).hexdigest()
                        fasta.write(f">{name}:{event['position0']}:{event['length']}\n{sequence}\n")
                output_records.append(obs)
    (args.output / "read_evidence.json").write_text(json.dumps(output_records, indent=2) + "\n")
    alt = counts["compatible_insertion"]
    ref = counts["reference_compatible_cigar"]
    result = {"scope": "CIGAR compatibility, not exact child allele or a sensitivity estimate",
        "anchor0": ANCHOR, "buffer_bed": [CHROM, *BUFFER], "core_bed": [CHROM, *CORE],
        "policy": {"mapq_min": 20, "min_aligned_bases_each_1000bp_flank": 500,
            "breakpoint_distance_max": 500, "insertion_length_bounds": INS_LENGTH},
        "bam_sha256": sha(args.bam), "counts": dict(counts), "excluded_records": dict(flags),
        "classified_alt_plus_ref": alt + ref,
        "raw_compatible_fraction": alt / (alt + ref) if alt + ref else None,
        "fraction_is_not_sniffles_vaf": True,
        "primary_names_with_external_sa": sum(any(o["sa_outside_buffer"] for o in v) for v in records.values()),
        "artifacts": {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)}
                      for p in args.output.iterdir() if p.is_file()}}
    (args.output / "census.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
