"""Fixed synthetic comparison to the previously tested bounded-line route."""
import io
import random

from analysis.stage_svpg_callsets import _stage_member


def test_streaming_and_legacy_agree_on_1000_fixed_synthetic_records():
    rng = random.Random(20261007)
    header = (b"##fileformat=VCFv4.2\n##contig=<ID=1,length=100000>\n"
              b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tHG002\n")
    for _ in range(1000):
        tokens = ["SVTYPE=INS", "FLAG", "OTHER=a=b",
                  "RNAMES=" + "r," * rng.randrange(100), "MYRNAMES=keep"]
        rng.shuffle(tokens)
        ending = rng.choice(["\n", "\r\n", ""])
        body = ("1\t200\t.\tA\t" + "AC" * rng.randrange(1, 100)
                + "\t.\tPASS\t" + ";".join(tokens) + "\tGT:DP\t0|1:10" + ending).encode()
        data, legacy, streamed = header + body, io.BytesIO(), io.BytesIO()
        left = _stage_member(io.BytesIO(data), legacy, [0, 100000])
        right = _stage_member(io.BytesIO(data), streamed, [0, 100000],
                              stream_rnames=True, chunk_size=rng.randrange(1, 100))
        assert legacy.getvalue() == streamed.getvalue()
        for key in ("source_sha256", "staged_sha256", "records", "decoded_bytes",
                    "omitted_RNAMES", "by_filter", "by_gt", "by_type"):
            assert left[key] == right[key]
