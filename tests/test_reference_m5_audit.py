import gzip
import hashlib

from scripts.audit_reference_m5 import compare, fasta_digests


def test_compare_distinguishes_case_sensitive_and_sam_canonical_md5(tmp_path):
    sequence = b"aCgTn"
    case_md5 = hashlib.md5(sequence).hexdigest()
    canonical_md5 = hashlib.md5(sequence.upper()).hexdigest()
    fasta = tmp_path / "ref.fa.gz"
    vcf = tmp_path / "truth.vcf.gz"
    sam_dict = tmp_path / "reads.dict"
    with gzip.open(fasta, "wb") as target:
        target.write(b">chr1 note\naCg\nTn\n")
    with gzip.open(vcf, "wt") as target:
        target.write(
            f"##contig=<ID=chr1,length=5,md5={case_md5}>\n"
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
        )
    sam_dict.write_text(f"@SQ\tSN:chr1\tLN:5\tM5:{canonical_md5}\n")

    result = compare(fasta, vcf, sam_dict)
    assert result["n_shared"] == 1
    assert result["n_vcf_matches_case_preserving"] == 1
    assert result["n_vcf_matches_canonical"] == 0
    assert result["n_dict_matches_canonical"] == 1
    assert result["n_lengths_match"] == 1


def test_fasta_digests_can_stop_after_first_contig(tmp_path):
    fasta = tmp_path / "two.fa.gz"
    with gzip.open(fasta, "wb") as target:
        target.write(b">chr1\naCgT\n>chr2\nGG\n")
    result = fasta_digests(fasta, stop_after="chr1")
    assert list(result) == ["chr1"]
    assert result["chr1"]["canonical_m5"] == hashlib.md5(b"ACGT").hexdigest()
