"""Exercise the extractor with a real, tiny synthetic indexed BAM, never study reads."""

import argparse
from array import array
import hashlib
import importlib.util
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extractor", type=Path, required=True)
    parser.add_argument("--reference-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if not args.output_dir.is_dir() or any(args.output_dir.iterdir()):
        raise ValueError("Existing empty fixture directory required")
    import pysam

    spec = importlib.util.spec_from_file_location("inv_trace_fixture_extractor", args.extractor)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reference = module.validate_reference_json(args.reference_json.read_bytes())
    dna = reference["dna"]
    header = {"HD": {"VN": "1.6", "SO": "coordinate"},
              "SQ": [{"SN": "chr2", "LN": module.CHR2_LENGTH}],
              "RG": [{"ID": "synthetic", "SM": "SYNTHETIC_NOT_STUDY_DNA"}]}
    bam = args.output_dir / "synthetic.bam"
    sequence = "AAAAA" + dna[10:40] + "CCCCC"
    reverse_sequence = dna[20:60]
    reverse_quality = "".join(chr(33 + value) for value in range(40))

    def record(name, flag, start, seq, cigar, qual, mapq):
        item = pysam.AlignedSegment()
        item.query_name, item.flag = name, flag
        item.reference_id, item.reference_start = 0, start
        item.mapping_quality, item.cigartuples = mapq, cigar
        item.query_sequence = seq
        item.query_qualities = pysam.qualitystring_to_array(qual)
        item.set_tag("RG", "synthetic")
        item.set_tag("HP", 1)
        item.set_tag("PS", 1)
        item.set_tag("ip", array("B", [1, 2, 3]))
        return item

    with pysam.AlignmentFile(str(bam), "wb", header=header) as handle:
        first = record("SYNTHETIC_FORWARD", 0, module.REGION_START + 10, sequence,
                       [(4, 5), (7, 30), (4, 5)], "I" * 40, 60)
        first.set_tag("SA", f"chr2,{module.REGION_START + 13},+,40M,0,0;")
        handle.write(first)
        handle.write(record("SYNTHETIC_FORWARD", 0x800, module.REGION_START + 12,
                            sequence, [(0, 40)], "I" * 40, 0))
        handle.write(record("SYNTHETIC_REVERSE", 0x10, module.REGION_START + 20,
                            reverse_sequence, [(7, 40)], reverse_quality, 60))
        missing = pysam.AlignedSegment()
        missing.query_name, missing.flag = "SYNTHETIC_MISSING_PAYLOAD", 0x800
        missing.reference_id, missing.reference_start = 0, module.REGION_START + 30
        missing.mapping_quality, missing.cigartuples = 0, [(5, 2), (0, 40)]
        missing.set_tag("RG", "synthetic")
        missing.set_tag("ip", array("B", [1, 2, 3]))
        handle.write(missing)
    pysam.index(str(bam))  # Synthetic fixture only. Never create a study BAM index.
    index = Path(str(bam) + ".bai")
    before = (sha(bam), sha(index))
    output = args.output_dir / "complete"
    output.mkdir()
    manifest, code = module.run_extraction(bam, args.reference_json, output, pysam_module=pysam)
    assert code == 0 and manifest["status"] == "COMPLETE"
    result = manifest["region_iteration"]
    assert result["region_iterator_eof_reached"] and result["records_written"] == 4
    assert result["unique_qnames"] == 3 and result["duplicate_qname_alignment_records"] == 1
    assert result["mapping_quality_counts_including_zero"] == {"60": 2, "0": 2}
    assert result["equals_reference_witness"]["equals_reference_bases_compared"] == 70
    assert result["equals_reference_witness"]["equals_reference_base_conflicts"] == 0
    rows = [json.loads(line) for line in (output / module.RECORDS_FILENAME).read_text().splitlines()][1:]
    assert rows[0]["forward_query_sequence_sha256_uppercase"] == rows[1]["forward_query_sequence_sha256_uppercase"]
    expected_reverse = reverse_sequence.translate(str.maketrans("ACGT", "TGCA"))[::-1]
    assert rows[2]["forward_query_sequence_sha256_uppercase"] == hashlib.sha256(expected_reverse.encode()).hexdigest()
    assert rows[2]["forward_query_quality_sha256"] == hashlib.sha256(reverse_quality[::-1].encode()).hexdigest()
    assert rows[3]["sequence_reference_oriented_bam"] is None
    assert rows[3]["quality_ascii_reference_oriented_bam"] is None
    assert rows[3]["full_query_payload_status"] == "UNKNOWN_HARD_CLIPPED_QUERY_BASES_NOT_STORED"
    assert all("ip" in row["omitted_tag_names_only"] for row in rows)
    assert before == (sha(bam), sha(index))
    try:
        module.run_extraction(bam, args.reference_json, output, pysam_module=pysam)
    except FileExistsError:
        pass
    else:
        raise AssertionError("Existing fixture output was not refused")

    no_index = args.output_dir / "unindexed.bam"
    with pysam.AlignmentFile(str(no_index), "wb", header=header):
        pass
    failed_output = args.output_dir / "missing-index"
    failed_output.mkdir()
    failure, code = module.run_extraction(no_index, args.reference_json, failed_output, pysam_module=pysam)
    assert code != 0 and failure["status"] == "FAILED"
    assert not failure["region_fetch_started"] and not Path(str(no_index) + ".bai").exists()
    receipt = {"status": "PASS", "scope": "SYNTHETIC_NATIVE_PYSAM_ABI_ONLY",
               "pysam_version": pysam.__version__, "records": 4,
               "study_bam_opened": False, "source_fixture_unchanged": before == (sha(bam), sha(index)),
               "extractor_sha256": sha(args.extractor)}
    with (args.output_dir / "fixture-check.json").open("x") as handle:
        json.dump(receipt, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
