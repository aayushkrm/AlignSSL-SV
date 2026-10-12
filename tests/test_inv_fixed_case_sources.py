"""Offline controls for the fixed INV-case source fetcher and VCF selector."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import pytest


ANALYSIS_DIR = Path(__file__).resolve().parents[1] / "analysis"
if str(ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_DIR))

import fetch_inv_fixed_case_sources as inv  # noqa: E402


class MockResponse:
    def __init__(self, body=b"", status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {}
        self.offset = 0
        self.read_calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size=-1):
        self.read_calls += 1
        if size is None or size < 0:
            size = len(self.body) - self.offset
        part = self.body[self.offset : self.offset + size]
        self.offset += len(part)
        return part


class FakeOpener:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, request, timeout):
        self.calls.append((request.full_url, timeout, request))
        if request.full_url not in self.responses:
            raise AssertionError(f"Unexpected URL request: {request.full_url}")
        response = self.responses[request.full_url]
        return response() if callable(response) else response


def _req_headers(request):
    return {key.lower(): value for key, value in request.header_items()}


def _git_blob_sha1(body):
    return hashlib.sha1(f"blob {len(body)}\0".encode() + body).hexdigest()


def _synthetic_vcf():
    records = [
        f"chr2\t{inv.WINDOW_LOW}\tpos-low\tN\t<INV>\t.\tPASS\tSVTYPE=INV;END={inv.WINDOW_LOW + 5}\tGT:DP\t0/1:8",
        f"2\t{inv.WINDOW_HIGH}\tpos-high\tN\t<INV>\t.\tPASS\tSVTYPE=INV;END={inv.WINDOW_HIGH}\tGT:DP\t1|0:9",
        f"chr2\t1\tend-low\tN\t<INV>\t.\tPASS\tSVTYPE=INV;END={inv.WINDOW_LOW}\tGT:DP\t0/1:4",
        f"chr2\t2\tend-high\tN\t<INV>\t.\tPASS\tSVTYPE=INV;END={inv.WINDOW_HIGH}\tGT:DP\t0/1:5",
        f"chr1\t500\tmate-window\tN\tN]chr2:{inv.WINDOW_LOW}]\t.\tPASS\tSVTYPE=BND\tGT:DP\t0/1:6",
        f"chr2\t{inv.WINDOW_LOW - 10}\tspans-target\tN\t<INV>\t.\tPASS\tSVTYPE=INV;END={inv.WINDOW_HIGH + 10}\tGT:DP\t0/1:3",
        f"chr1\t{inv.WINDOW_LOW}\tother-chromosome\tN\t<INV>\t.\tPASS\tSVTYPE=INV;END={inv.WINDOW_HIGH}\tGT:DP\t0/1:2",
    ]
    headers = [
        "##fileformat=VCFv4.2",
        "##reference=synthetic-reference-label",
        "##contig=<ID=chr2,length=242193529>",
        "##SAMPLE=<ID=HG002>",
        "##source=synthetic-test-caller",
        "##version=synthetic-1",
        "##bcftools_viewVersion=1.20",
        "##fileDate=20261013",
        "##command=synthetic --mode test",
        "##commandline=synthetic --commandline",
        "##cmdline=synthetic --cmdline",
        "##bcftools_viewCommand=bcftools view --synthetic",
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tHG002",
    ]
    return ("\n".join(headers + records) + "\n").encode("utf-8")


def _fixture_bodies():
    vcf = _synthetic_vcf()
    return {
        item["path"]: (gzip.compress(vcf, mtime=0) if item["path"].endswith(".gz") else vcf)
        for item in inv.expected_sources()
    }


def _tree_document(bodies, overrides=None, *, truncated=False):
    overrides = overrides or {}
    tree = []
    for item in inv.expected_sources():
        body = bodies[item["path"]]
        size, sha = overrides.get(item["path"], (len(body), _git_blob_sha1(body)))
        tree.append({"path": item["path"], "type": "blob", "size": size, "sha": sha})
    tree.extend(
        {"path": f"unrelated/{index:03d}.txt", "type": "blob", "size": 1, "sha": "0" * 40}
        for index in range(inv.EXPECTED_TREE_ENTRIES - len(tree))
    )
    return {"truncated": truncated, "tree": tree}


def _headers_for_bytes(body):
    return {"Content-Length": str(len(body)), "Content-Encoding": "identity"}


def _fixture_opener(bodies, tree_document=None):
    tree_document = tree_document or _tree_document(bodies)
    tree_body = json.dumps(tree_document, separators=(",", ":")).encode()
    responses = {inv.TREE_URL: MockResponse(tree_body, headers=_headers_for_bytes(tree_body))}
    for path, body in bodies.items():
        url = inv.raw_url_for(path)
        responses[url] = MockResponse(body, headers=_headers_for_bytes(body))
    opener = FakeOpener(responses)
    return opener


def _patch_expected_sums(monkeypatch, bodies):
    caller_total = sum(len(bodies[path]) for path in inv.PRIMARY_PATHS + inv.SUPPLEMENTAL_PATHS)
    truth_total = sum(len(bodies[path]) for path in inv.TRUTH_PATHS)
    monkeypatch.setattr(inv, "EXPECTED_CALLER_BYTES", caller_total)
    monkeypatch.setattr(inv, "EXPECTED_TRUTH_BYTES", truth_total)


def test_frozen_inventory_has_20_long_read_2_supplemental_and_3_truth_files():
    sources = inv.expected_sources()

    assert len(inv.PRIMARY_PATHS) == 20
    assert len(inv.SUPPLEMENTAL_PATHS) == 2
    assert len(inv.TRUTH_PATHS) == 3
    assert len(sources) == 25
    assert len({item["path"] for item in sources}) == 25
    assert all(path.startswith(inv.CALLSET_DIRECTORY) for path in inv.PRIMARY_PATHS)
    assert inv.SUPPLEMENTAL_PATHS == (
        inv.CALLSET_DIRECTORY + "gridss2_inv.vcf",
        inv.CALLSET_DIRECTORY + "manta_inv.vcf",
    )
    assert inv.TRUTH_PATHS == (
        inv.TRUTH_DIRECTORY + "HG002_T2Tv1.1_asm_ref_2aligners.merged.vcf.gz",
        inv.TRUTH_DIRECTORY + "HG002_T2Tv1.1_asm_ref_2aligners.merged.vcf_Tier1.vcf.gz",
        inv.TRUTH_DIRECTORY + "HG002_T2Tv1.1_asm_ref_2aligners.merged.vcf_Tier2.vcf.gz",
    )
    assert inv.CASE_START == 240_685_775
    assert inv.CASE_END == 240_688_980
    assert inv.WINDOW_LOW == 240_684_775
    assert inv.WINDOW_HIGH == 240_689_980


def test_pinned_tree_validation_selects_only_exact_paths_and_uses_git_blob_metadata(monkeypatch):
    bodies = _fixture_bodies()
    _patch_expected_sums(monkeypatch, bodies)
    tree = _tree_document(bodies)

    selected = inv._validate_tree_entries(tree)

    assert [item["path"] for item in selected] == [item["path"] for item in inv.expected_sources()]
    assert all(item["raw_url"].startswith(inv.RAW_BASE) for item in selected)
    assert all(item["size"] == len(bodies[item["path"]]) for item in selected)
    assert all(item["git_blob_sha1"] == _git_blob_sha1(bodies[item["path"]]) for item in selected)
    assert len(tree["tree"]) == 603


@pytest.mark.parametrize(
    "document_change",
    [
        lambda document: document.update(truncated=True),
        lambda document: document["tree"].pop(0),
        lambda document: document["tree"][0].update(type="tree"),
    ],
    ids=["truncated-tree", "missing-exact-path", "path-not-a-blob"],
)
def test_tree_validation_rejects_incomplete_or_nonblob_inventory(monkeypatch, document_change):
    bodies = _fixture_bodies()
    _patch_expected_sums(monkeypatch, bodies)
    document = _tree_document(bodies)
    document_change(document)

    with pytest.raises(ValueError):
        inv._validate_tree_entries(document)


def test_metadata_limit_rejects_declared_oversize_before_read():
    response = MockResponse(
        b"x" * 4,
        headers={"Content-Length": str(inv.METADATA_CAP_BYTES + 1)},
    )

    with pytest.raises(ValueError, match="metadata exceeds"):
        inv.read_metadata_response(response)

    assert response.read_calls == 0


@pytest.mark.parametrize("limit_kind", ["individual", "cumulative"], ids=["file-cap", "total-cap"])
def test_tree_size_caps_fail_before_any_source_body_request(monkeypatch, tmp_path, limit_kind):
    bodies = _fixture_bodies()
    if limit_kind == "individual":
        over = {inv.PRIMARY_PATHS[0]: (inv.SOURCE_FILE_CAP_BYTES + 1, "1" * 40)}
    else:
        over = {
            item["path"]: (300_000, "1" * 40)
            for item in inv.expected_sources()
        }
    tree = _tree_document(bodies, overrides=over)
    tree_body = json.dumps(tree).encode()
    opener = FakeOpener({
        inv.TREE_URL: MockResponse(tree_body, headers=_headers_for_bytes(tree_body)),
    })
    monkeypatch.setattr(inv, "EXPECTED_CALLER_BYTES", 6_065_007)
    monkeypatch.setattr(inv, "EXPECTED_TRUTH_BYTES", 22_698)

    with pytest.raises(ValueError, match="cap"):
        inv.fetch_sources(tmp_path, opener=opener)

    assert [url for url, _, _ in opener.calls] == [inv.TREE_URL]


def test_source_reader_enforces_size_caps_short_and_overlong_bodies():
    at_file_cap = b"x" * inv.SOURCE_FILE_CAP_BYTES
    valid = MockResponse(at_file_cap, headers={"Content-Length": str(len(at_file_cap))})
    assert inv.read_source_response(valid, len(at_file_cap)) == at_file_cap
    assert valid.read_calls == len(at_file_cap) // inv.READ_CHUNK_BYTES

    too_large = MockResponse()
    with pytest.raises(ValueError, match="individual cap"):
        inv.read_source_response(too_large, inv.SOURCE_FILE_CAP_BYTES + 1)
    assert too_large.read_calls == 0

    cumulative = MockResponse()
    with pytest.raises(ValueError, match="cumulative cap"):
        inv.read_source_response(
            cumulative,
            8,
            transferred_before=inv.SOURCE_TOTAL_CAP_BYTES - 8,
        )
    assert cumulative.read_calls == 0

    wrong_length = MockResponse(b"abc", headers={"Content-Length": "3"})
    with pytest.raises(ValueError, match="Content-Length"):
        inv.read_source_response(wrong_length, 4)
    assert wrong_length.read_calls == 0

    short = MockResponse(b"abc", headers={"Content-Length": "4"})
    with pytest.raises(ValueError, match="ended before"):
        inv.read_source_response(short, 4)
    assert short.read_calls == 2

    overlong = MockResponse(b"abcde")
    with pytest.raises(ValueError, match="exceeds the pinned"):
        inv.read_source_response(overlong, 4)
    assert overlong.read_calls == 2


def test_response_status_and_content_encoding_are_checked_before_body_read():
    for response in (
        MockResponse(b"body", status=206, headers={"Content-Length": "4"}),
        MockResponse(
            b"body",
            headers={"Content-Length": "4", "Content-Encoding": "gzip"},
        ),
    ):
        with pytest.raises(ValueError):
            inv.read_source_response(response, 4)
        assert response.read_calls == 0


def test_git_blob_sha1_validation_catches_body_change():
    body = b"known source bytes"
    sha = _git_blob_sha1(body)

    assert inv.verify_git_blob("fixture.vcf", body, len(body), sha) == sha
    with pytest.raises(ValueError, match="SHA-1 mismatch"):
        inv.verify_git_blob("fixture.vcf", body + b"!", len(body) + 1, sha)


def test_offline_fetch_saves_exact_sources_hashes_headers_records_and_gzip_crc(monkeypatch, tmp_path):
    bodies = _fixture_bodies()
    _patch_expected_sums(monkeypatch, bodies)
    opener = _fixture_opener(bodies)

    manifest = inv.fetch_sources(tmp_path, opener=opener)

    assert manifest["status"] == "COMPLETE"
    assert manifest["scientific_recovery_claim"] == "NOT_ASSESSED"
    assert manifest["retrieval"]["tree_metadata_bytes"] <= inv.METADATA_CAP_BYTES
    assert manifest["retrieval"]["source_bytes_transferred"] == sum(map(len, bodies.values()))
    assert [source["path"] for source in manifest["sources"]] == [
        item["path"] for item in inv.expected_sources()
    ]
    assert [url for url, _, _ in opener.calls] == [
        inv.TREE_URL,
        *(inv.raw_url_for(item["path"]) for item in inv.expected_sources()),
    ]
    assert all(timeout == 25 for _, timeout, _ in opener.calls)
    assert all(_req_headers(request)["accept-encoding"] == "identity" for _, _, request in opener.calls)
    for source in manifest["sources"]:
        body = bodies[source["path"]]
        assert source["download_status"] == "VALIDATED"
        assert source["downloaded_bytes"] == len(body)
        assert source["sha256"] == hashlib.sha256(body).hexdigest()
        assert source["git_blob_sha1_verified"] is True
        assert (tmp_path / source["local_filename"]).read_bytes() == body
        summary = source["vcf_summary"]
        assert summary["total_records_read"] == 7
        if source["path"].endswith(".gz"):
            assert summary["gzip_crc_verified"] is True
        else:
            assert summary["gzip_crc_verified"] is None
    assert all(
        source["vcf_summary"]["nearby_records"][0]["fields"][4] == "<INV>"
        for source in manifest["sources"]
    )


def test_local_cli_revision_reuses_all_sources_and_changes_only_header_metadata(
    monkeypatch, tmp_path, capsys
):
    bodies = _fixture_bodies()
    _patch_expected_sums(monkeypatch, bodies)
    source_dir = tmp_path / "retained"
    source_dir.mkdir()
    original = inv.fetch_sources(source_dir, opener=_fixture_opener(bodies))
    aliases = {
        "##commandline=": "command",
        "##cmdline=": "command",
        "##bcftools_viewCommand=": "command",
        "##bcftools_viewVersion=": "version",
    }
    for source in original["sources"]:
        summary = source["vcf_summary"]
        kept_headers = []
        for line in summary["relevant_headers"]:
            prefix = next((key for key in aliases if line.startswith(key)), None)
            if prefix is None:
                kept_headers.append(line)
            else:
                summary["header_counts"][aliases[prefix]] -= 1
        summary["relevant_headers"] = kept_headers

    original_path = tmp_path / "sources.json"
    original_path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
    original_bytes = original_path.read_bytes()
    source_bytes_before = {
        source["local_filename"]: (source_dir / source["local_filename"]).read_bytes()
        for source in original["sources"]
    }
    output_path = tmp_path / "sources_with_commands.json"
    attempts_path = tmp_path / "first-attempts.txt"

    def forbid_network(*_args, **_kwargs):
        raise AssertionError("local revision attempted a network request")

    monkeypatch.setattr(inv.urllib.request, "urlopen", forbid_network)
    monkeypatch.setattr(sys, "argv", [
        "fetch_inv_fixed_case_sources.py",
        "--from-manifest", str(original_path),
        "--manifest", str(output_path),
        "--first-attempts", str(attempts_path),
    ])
    inv.main()
    capsys.readouterr()

    corrected = json.loads(output_path.read_text(encoding="utf-8"))
    assert original_path.read_bytes() == original_bytes
    assert corrected["revision"]["kind"] == "LOCAL_ONLY_HEADER_METADATA_CORRECTION"
    assert corrected["revision"]["original_manifest_sha256"] == hashlib.sha256(original_bytes).hexdigest()
    assert corrected["revision"]["source_bodies_reused_without_modification"] is True
    assert corrected["revision"]["selection_coordinates_hashes_and_records_unchanged"] is True
    assert corrected["revision"]["header_aliases_added"] == {
        "commandline": 25,
        "cmdline": 25,
        "bcftools_viewCommand": 25,
        "bcftools_viewVersion": 25,
    }
    assert corrected["retrieval"]["source_bytes_transferred"] == original["retrieval"]["source_bytes_transferred"]
    assert corrected["retrieval"]["new_operation_network_bytes"] == 0
    assert corrected["revision"]["new_operation_network_bytes"] == 0
    assert corrected["case"] == original["case"]
    assert corrected["sources"] == [
        {
            **old_source,
            "vcf_summary": {
                **old_source["vcf_summary"],
                "relevant_headers": new_source["vcf_summary"]["relevant_headers"],
                "header_counts": new_source["vcf_summary"]["header_counts"],
            },
        }
        for old_source, new_source in zip(original["sources"], corrected["sources"])
    ]
    for source in corrected["sources"]:
        summary = source["vcf_summary"]
        assert summary["header_counts"]["command"] == 4
        assert summary["header_counts"]["version"] == 2
        assert all(any(line.startswith(prefix) for line in summary["relevant_headers"])
                   for prefix in aliases)
        assert (source_dir / source["local_filename"]).read_bytes() == source_bytes_before[source["local_filename"]]

    notes = attempts_path.read_text(encoding="utf-8")
    assert "##commandline" in notes and "##cmdline" in notes
    assert "##bcftools_viewCommand" in notes and "##bcftools_viewVersion" in notes
    assert "backslash and zero" in notes
    assert "all 25 retained source files" in notes


def test_local_revision_refuses_existing_outputs_without_overwriting(tmp_path):
    original_path = tmp_path / "original.json"
    original_path.write_text("not parsed because output already exists", encoding="utf-8")
    output_path = tmp_path / "corrected.json"
    output_path.write_text("preserve this", encoding="utf-8")
    attempts_path = tmp_path / "first-attempts.txt"

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        inv.regenerate_local_revision(original_path, output_path, attempts_path)

    assert output_path.read_text(encoding="utf-8") == "preserve this"
    assert not attempts_path.exists()


def test_fetch_refuses_nonempty_output_dir_before_metadata_request(tmp_path):
    (tmp_path / "existing.vcf").write_bytes(b"keep")
    opener = FakeOpener({})

    with pytest.raises(ValueError, match="must be empty"):
        inv.fetch_sources(tmp_path, opener=opener)

    assert opener.calls == []
    assert (tmp_path / "existing.vcf").read_bytes() == b"keep"


def test_selector_uses_inclusive_pos_end_and_mate_endpoints_and_separates_spanning():
    summary = inv.summarize_vcf_body(_synthetic_vcf(), "fixture.vcf")

    assert summary["total_records_read"] == 7
    assert [record["id"] for record in summary["nearby_records"]] == [
        "pos-low",
        "pos-high",
        "end-low",
        "end-high",
        "mate-window",
    ]
    assert [record["id"] for record in summary["spanning_records"]] == ["spans-target"]
    assert "spans-target" not in [record["id"] for record in summary["nearby_records"]]
    assert "other-chromosome" not in [record["id"] for record in summary["nearby_records"]]
    assert summary["nearby_records"][0]["raw_record"].startswith("chr2\t240684775\tpos-low")
    assert summary["nearby_records"][0]["fields"][8:] == ["GT:DP", "0/1:8"]
    assert summary["nearby_records"][1]["fields"][9] == "1|0:9"
    assert summary["header_counts"] == {
        "fileformat": 1,
        "reference": 1,
        "contig": 1,
        "sample": 1,
        "source": 1,
        "version": 2,
        "date": 1,
        "command": 4,
        "chrom_columns": 1,
    }
    assert "##reference=synthetic-reference-label" in summary["relevant_headers"]
    assert "##command=synthetic --mode test" in summary["relevant_headers"]
    assert "##commandline=synthetic --commandline" in summary["relevant_headers"]
    assert "##cmdline=synthetic --cmdline" in summary["relevant_headers"]
    assert "##bcftools_viewCommand=bcftools view --synthetic" in summary["relevant_headers"]
    assert "##bcftools_viewVersion=1.20" in summary["relevant_headers"]


def test_malformed_vcf_is_reported_after_the_full_stream_is_counted():
    later_record = f"chr2\t{inv.CASE_START}\tvalid-later\tN\t<INV>\t.\tPASS\tEND={inv.CASE_END}\n"
    source = (
        b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
        b"chr2\tbad-pos\tid\tN\t<INV>\t.\tPASS\tEND=9\n"
        + later_record.encode()
    )

    class EofTrackingStream(io.BytesIO):
        eof_seen = False

        def readline(self, size=-1):
            line = super().readline(size)
            if not line:
                self.eof_seen = True
            return line

    stream = EofTrackingStream(source)
    with pytest.raises(inv.VCFFormatError, match="POS is not a positive integer") as caught:
        inv.scan_vcf_stream(stream, "malformed.vcf")

    assert stream.eof_seen
    assert caught.value.summary["total_records_read"] == 2
    assert caught.value.summary["nearby_records"][0]["id"] == "valid-later"
    assert caught.value.summary["malformed_records"][0]["line_number"] == 2


@pytest.mark.parametrize(
    "record",
    [
        "chr2\t1\tshort",
        "chr2\t0\tid\tN\t<INV>\t.\tPASS\tEND=10",
        "chr2\t1\tid\tN\t<INV>\t.\tPASS\tEND=bad",
    ],
    ids=["too-few-fields", "nonpositive-pos", "malformed-end"],
)
def test_vcf_malformed_records_are_rejected(record):
    body = ("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n" + record + "\n").encode()
    with pytest.raises(inv.VCFFormatError):
        inv.summarize_vcf_body(body, "bad.vcf")


def test_gzip_vcf_must_reach_valid_crc_and_eof():
    good = gzip.compress(_synthetic_vcf(), mtime=0)
    result = inv.summarize_vcf_body(good, "truth.vcf.gz")
    assert result["gzip_crc_verified"] is True
    assert result["total_records_read"] == 7

    bad_crc = bytearray(good)
    bad_crc[-8] ^= 1
    with pytest.raises(gzip.BadGzipFile, match="CRC"):
        inv.summarize_vcf_body(bytes(bad_crc), "bad-crc.vcf.gz")

    with pytest.raises((EOFError, gzip.BadGzipFile)):
        inv.summarize_vcf_body(good[:-5], "truncated.vcf.gz")
