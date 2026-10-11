import gzip
import hashlib
import io
import json
import tarfile

import pytest

from scripts.audit_verified_local_tar import audit_tar, read_table_header, write_report


REQUIRED_COLUMNS = frozenset({"sample_id", "value"})
ALLOWED_COLUMNS = frozenset({"sample_id", "value", "score"})


def make_tar(entries, tar_format=tarfile.USTAR_FORMAT):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w", format=tar_format) as archive:
        for name, data in entries:
            if isinstance(data, tarfile.TarInfo):
                item = data
                item.name = name
                archive.addfile(item)
            else:
                item = tarfile.TarInfo(name)
                item.size = len(data)
                archive.addfile(item, io.BytesIO(data))
    return stream.getvalue()


def write_archive(tmp_path, payload, name="source.tar"):
    path = tmp_path / name
    path.write_bytes(payload)
    return path, len(payload), hashlib.md5(payload).hexdigest()


def audit_selected(path, size, md5, member, **kwargs):
    return audit_tar(
        path, size, md5, table_member=member,
        required_columns=REQUIRED_COLUMNS, allowed_columns=ALLOWED_COLUMNS,
        **kwargs,
    )


def test_inventory_then_selected_nested_csv_gzip_header(tmp_path):
    body = b"sample_id\tvalue\n\xffPRIVATE BODY MUST NOT BE DECODED\n"
    tables_directory = tarfile.TarInfo("tables/")
    tables_directory.type = tarfile.DIRTYPE
    payload = make_tar([
        ("tables/", tables_directory),
        ("tables/records.csv.gz", gzip.compress(body)),
        ("code.py", b"raise AssertionError('must not execute')"),
    ])
    path, size, md5 = write_archive(tmp_path, payload, "source.tar")

    inventory = audit_tar(path, size, md5)
    assert inventory["scan_stage"] == "INVENTORY"
    assert inventory["table_header"] is None
    assert inventory["member_count"] == 3
    assert inventory["members"][0]["type"] == "directory"
    assert inventory["inspected_records"] == 0
    assert inventory["tar_integrity_status"] == "VERIFIED"

    report = audit_selected(
        path, size, md5, "tables/records.csv.gz",
        source_url="https://user:password@example.test/source.tar?token=redact#fragment",
    )
    counts = report["decompression_counts"]
    assert report["whole_archive_md5_verification"] == "VERIFIED"
    assert report["sha256"] == hashlib.sha256(payload).hexdigest()
    assert report["scan_stage"] == "HEADER_INSPECTION"
    assert report["acquisition_identity_status"] == "VERIFIED"
    assert report["acquisition_identity"]["actual_size_bytes"] == size
    assert report["acquisition_identity"]["sha256"] == hashlib.sha256(payload).hexdigest()
    assert report["tar_integrity_status"] == "VERIFIED"
    assert report["outer_gzip_integrity"] == "NOT_APPLICABLE"
    assert report["inspected_nested_gzip_integrity"] == "VERIFIED"
    assert report["table_header"]["fieldnames"] == ["sample_id", "value"]
    assert report["column_signature"] == {
        "required_columns": ["sample_id", "value"],
        "allowed_columns": ["sample_id", "score", "value"],
    }
    assert report["table_header"]["delimiter"] == "\t"
    assert report["table_header"]["data_rows_parsed"] == 0
    assert report["table_header"]["retained_header_metadata_bytes"] <= 64 * 1_024
    assert report["inspected_records"] == report["table_data_rows_parsed"] == 0
    assert counts["outer_tar_stream_bytes"] == len(payload)
    assert counts["nested_csv_gzip_output_bytes"] == len(body)
    assert counts["aggregate_output_bytes"] == len(payload) + len(body)
    assert report["aggregate_decompressed_bytes"] == counts["aggregate_output_bytes"]
    assert report["limits"]["aggregate_decompressed_bytes"] == 250 * 1_048_576
    assert report["source_url"] == "https://example.test/source.tar"
    assert report["source_url_redacted"]
    assert "password" not in json.dumps(report)
    assert "token=redact" not in json.dumps(report)
    assert "PRIVATE BODY" not in json.dumps(report)
    assert not report["member_files_written_to_disk"]
    assert not report["archive_code_executed"]


def test_outer_gzip_tar_is_drained_and_integrity_reported(tmp_path):
    plain_tar = make_tar([("small.bin", b"metadata only")])
    payload = gzip.compress(plain_tar)
    path, size, md5 = write_archive(tmp_path, payload, "source.tar.gz")

    report = audit_tar(path, size, md5)

    assert report["archive_format"] == "tar.gz"
    assert report["tar_integrity_status"] == "VERIFIED"
    assert report["outer_gzip_integrity"] == "VERIFIED"
    assert report["inspected_nested_gzip_integrity"] == "NOT_INSPECTED"
    assert report["decompression_counts"]["outer_tar_stream_bytes"] == len(plain_tar)


def test_accepts_standard_gnu_regular_header_without_extensions(tmp_path):
    payload = make_tar([("ordinary.bin", b"metadata")], tarfile.GNU_FORMAT)
    path, size, md5 = write_archive(tmp_path, payload, "gnu-standard.tar")

    report = audit_tar(path, size, md5)

    assert report["tar_integrity_status"] == "VERIFIED"
    assert report["members"] == [{"name": "ordinary.bin", "type": "file", "size": 8}]


def test_outer_gzip_crc_failure_does_not_report_integrity_pass(tmp_path):
    payload = bytearray(gzip.compress(make_tar([("small.bin", b"x")])))
    payload[-1] ^= 0x01
    path, size, md5 = write_archive(tmp_path, bytes(payload), "bad.tar.gz")
    with pytest.raises(ValueError, match="Outer gzip TAR failed integrity"):
        audit_tar(path, size, md5)


def test_nested_gzip_crc_is_checked_after_header(tmp_path):
    nested = bytearray(gzip.compress(b"sample_id,value\nrow,1\n"))
    nested[-8] ^= 0x01
    path, size, md5 = write_archive(
        tmp_path, make_tar([("table.csv.gz", bytes(nested))]))
    with pytest.raises(ValueError, match="nested gzip CSV failed integrity"):
        audit_selected(path, size, md5, "table.csv.gz")


def test_plain_csv_header_reads_only_the_first_line():
    stream = io.BytesIO(b'"sample,id",score\nprivate row\n')
    header = read_table_header(
        stream, frozenset({"sample,id", "score"}),
        frozenset({"sample,id", "score"}),
    )
    assert header["fieldnames"] == ["sample,id", "score"]
    assert header["delimiter"] == ","
    assert header["data_rows_parsed"] == 0
    assert stream.read() == b"private row\n"


def test_opt_in_command_comment_is_hashed_not_retained():
    comment = b"# eval_accuracy.py PRIVATE_COMMAND_ARGUMENT\n"
    stream = io.BytesIO(comment + b"sample_id,value\n\xffPRIVATE_BODY\n")
    header = read_table_header(
        stream, REQUIRED_COLUMNS, ALLOWED_COLUMNS,
        allow_leading_command_comment=True,
    )
    assert header["leading_command_comment_bytes"] == len(comment)
    assert header["leading_command_comment_sha256"] == hashlib.sha256(comment).hexdigest()
    assert not header["leading_command_comment_content_retained"]
    assert header["fieldnames"] == ["sample_id", "value"]
    assert "PRIVATE" not in json.dumps(header)
    assert stream.read() == b"\xffPRIVATE_BODY\n"


@pytest.mark.parametrize("allow_comment", [False, True])
def test_comment_does_not_enable_headerless_records(allow_comment):
    stream = io.BytesIO(b"# command\nHG002,BRCA1,alleleA,alleleB\n")
    with pytest.raises(ValueError) as error:
        read_table_header(
            stream, REQUIRED_COLUMNS, ALLOWED_COLUMNS,
            allow_leading_command_comment=allow_comment,
        )
    assert "HG002" not in str(error.value)
    assert "BRCA1" not in str(error.value)


def test_only_one_command_comment_may_precede_header():
    stream = io.BytesIO(b"# first\n# second SECRET\nsample_id,value\n")
    with pytest.raises(ValueError) as error:
        read_table_header(
            stream, REQUIRED_COLUMNS, ALLOWED_COLUMNS,
            allow_leading_command_comment=True,
        )
    assert "SECRET" not in str(error.value)


def test_comment_and_header_share_byte_cap():
    stream = io.BytesIO(b"# command\nsample_id,value\n")
    with pytest.raises(ValueError, match="byte limit"):
        read_table_header(
            stream, REQUIRED_COLUMNS, ALLOWED_COLUMNS, max_bytes=20,
            allow_leading_command_comment=True,
        )


def test_long_or_unterminated_comment_fails_closed():
    stream = io.BytesIO(b"# " + b"x" * 20)
    with pytest.raises(ValueError, match="comment exceeds"):
        read_table_header(
            stream, REQUIRED_COLUMNS, ALLOWED_COLUMNS, max_bytes=20,
            allow_leading_command_comment=True,
        )


def test_nested_comment_header_still_validates_stream_without_body_parsing(tmp_path):
    body = b"# command SECRET\nsample_id,value\n\xffPRIVATE_BODY\n"
    path, size, md5 = write_archive(
        tmp_path, make_tar([("table.csv.gz", gzip.compress(body))]))
    report = audit_selected(
        path, size, md5, "table.csv.gz", allow_leading_command_comment=True,
    )
    assert report["inspected_nested_gzip_integrity"] == "VERIFIED"
    assert report["table_data_rows_parsed"] == 0
    assert "PRIVATE" not in json.dumps(report)
    assert "SECRET" not in json.dumps(report)
    with pytest.raises(ValueError, match="selected table"):
        audit_tar(path, size, md5, allow_leading_command_comment=True)


@pytest.mark.parametrize(
    "header,match",
    [
        (b"123,456\n", "numeric"),
        (b"a,a\n", "duplicate field name"),
        (b"singlefield\n", "no detectable delimiter"),
        (b"VISIBLE_SECRET,\xff\n", "not valid UTF-8"),
    ],
)
def test_malformed_or_ambiguous_headers_fail_without_echoing_content(header, match):
    with pytest.raises(ValueError, match=match) as error:
        read_table_header(
            io.BytesIO(header), frozenset({"alpha", "beta"}),
            frozenset({"alpha", "beta"}),
        )
    assert "VISIBLE_SECRET" not in str(error.value)


def test_headerless_record_does_not_match_frozen_signature():
    with pytest.raises(ValueError, match="required columns") as error:
        read_table_header(
            io.BytesIO(b"HG002,BRCA1,alleleA,alleleB\n"),
            REQUIRED_COLUMNS, ALLOWED_COLUMNS,
        )
    assert "HG002" not in str(error.value)
    assert "BRCA1" not in str(error.value)


def test_unknown_column_fails_without_echoing_its_name():
    with pytest.raises(ValueError, match="unrecognized field names") as error:
        read_table_header(
            io.BytesIO(b"sample_id,value,SECRET_COLUMN\n"),
            REQUIRED_COLUMNS, ALLOWED_COLUMNS,
        )
    assert "SECRET_COLUMN" not in str(error.value)


def test_header_mode_requires_both_signatures(tmp_path):
    path, size, md5 = write_archive(
        tmp_path, make_tar([("table.csv", b"sample_id,value\n")]))
    with pytest.raises(ValueError, match="requires required and allowed"):
        audit_tar(path, size, md5, table_member="table.csv")


@pytest.mark.parametrize(
    "name", ["../outside.csv", "/absolute.csv", "folder/../../outside.csv"]
)
def test_rejects_unsafe_paths(tmp_path, name):
    path, size, md5 = write_archive(tmp_path, make_tar([(name, b"a,b\n")]))
    with pytest.raises(ValueError, match="Unsafe TAR member path"):
        audit_tar(path, size, md5)


def test_rejects_duplicate_names_including_normalized_aliases(tmp_path):
    payload = make_tar([("tables//x.csv", b"a,b\n"), ("tables/x.csv", b"c,d\n")])
    path, size, md5 = write_archive(tmp_path, payload)
    with pytest.raises(ValueError, match="Duplicate TAR member"):
        audit_tar(path, size, md5)


@pytest.mark.parametrize(
    "member_type,match",
    [
        (tarfile.SYMTYPE, "TAR links"),
        (tarfile.LNKTYPE, "TAR links"),
        (tarfile.FIFOTYPE, "TAR device"),
    ],
)
def test_rejects_links_and_devices(tmp_path, member_type, match):
    item = tarfile.TarInfo("link")
    item.type = member_type
    item.linkname = "elsewhere"
    path, size, md5 = write_archive(tmp_path, make_tar([("link", item)]))
    with pytest.raises(ValueError, match=match):
        audit_tar(path, size, md5)


def test_rejects_sparse_and_tar_extension_records(tmp_path):
    sparse = tarfile.TarInfo("sparse.bin")
    sparse.type = b"S"
    sparse_tar = make_tar([("sparse.bin", sparse)])
    path, size, md5 = write_archive(tmp_path, sparse_tar, "sparse.tar")
    with pytest.raises(ValueError, match="Sparse TAR"):
        audit_tar(path, size, md5)

    pax_item = tarfile.TarInfo("table.csv")
    pax_item.size = len(b"a,b\n")
    pax_item.pax_headers = {"comment": "synthetic extension fixture"}
    pax_tar = make_tar([("table.csv", pax_item)], tarfile.PAX_FORMAT)
    pax_path, pax_size, pax_md5 = write_archive(tmp_path, pax_tar, "pax.tar")
    with pytest.raises(ValueError, match="extension records"):
        audit_tar(pax_path, pax_size, pax_md5)

    long_name = "a" * 110 + ".csv"
    gnu_tar = make_tar([(long_name, b"a,b\n")], tarfile.GNU_FORMAT)
    gnu_path, gnu_size, gnu_md5 = write_archive(tmp_path, gnu_tar, "gnu.tar")
    with pytest.raises(ValueError, match="extension records"):
        audit_tar(gnu_path, gnu_size, gnu_md5)


def test_safe_directory_allowed_but_selected_header_must_be_file(tmp_path):
    directory = tarfile.TarInfo("table.csv")
    directory.type = tarfile.DIRTYPE
    path, size, md5 = write_archive(
        tmp_path, make_tar([("table.csv", directory)]))
    report = audit_tar(path, size, md5)
    assert report["members"][0]["type"] == "directory"
    with pytest.raises(ValueError, match="not a regular file"):
        audit_selected(path, size, md5, "table.csv")


def test_size_and_md5_fail_before_tar_inspection(tmp_path):
    path, size, md5 = write_archive(tmp_path, make_tar([("table.csv", b"a,b\n")]))
    with pytest.raises(ValueError, match="size differs"):
        audit_tar(path, size + 1, md5)
    with pytest.raises(ValueError, match="MD5 differs"):
        audit_tar(path, size, "0" * 32)


def test_rejects_oversized_header_line(tmp_path):
    oversized = b"x" * (64 * 1_024 + 1) + b"\n"
    path, size, md5 = write_archive(
        tmp_path, make_tar([("table.csv", oversized)]))
    with pytest.raises(ValueError, match="header line exceeds"):
        audit_selected(path, size, md5, "table.csv")


def test_nested_csv_output_counts_against_aggregate_budget(tmp_path):
    nested = gzip.compress(b"sample_id,value\n" + b"row,1\n" * 2_000)
    path, size, md5 = write_archive(
        tmp_path, make_tar([("table.csv.gz", nested)]))
    with pytest.raises(ValueError, match="Aggregate decompression budget"):
        audit_selected(path, size, md5, "table.csv.gz",
                       max_uncompressed_tar_bytes=12_000)


def test_declared_member_bytes_and_member_count_are_capped(tmp_path):
    path, size, md5 = write_archive(
        tmp_path, make_tar([("large.bin", b"x" * 20_000)]))
    with pytest.raises(ValueError, match="aggregate decompression limit"):
        audit_tar(path, size, md5, max_uncompressed_tar_bytes=15_000)

    many_path, many_size, many_md5 = write_archive(
        tmp_path, make_tar([(f"file-{index}.bin", b"") for index in range(3)]),
        "many.tar",
    )
    with pytest.raises(ValueError, match="member count"):
        audit_tar(many_path, many_size, many_md5, max_members=2)


def test_archive_byte_limit_is_enforced(tmp_path):
    path, size, md5 = write_archive(tmp_path, make_tar([("small.bin", b"x")]))
    with pytest.raises(ValueError, match="archive-byte limit"):
        audit_tar(path, size, md5, max_archive_bytes=size - 1)


def test_report_creation_is_exclusive_and_checksummed(tmp_path):
    out = tmp_path / "report.json"
    report = {"purpose": "synthetic metadata"}
    write_report(out, report)
    data = out.read_bytes()
    sidecar = out.with_suffix(".json.sha256")
    assert sidecar.read_text().split()[0] == hashlib.sha256(data).hexdigest()
    with pytest.raises(FileExistsError):
        write_report(out, report)


def test_dangling_checksum_symlink_prevents_partial_output(tmp_path):
    out = tmp_path / "report.json"
    out.with_suffix(".json.sha256").symlink_to(tmp_path / "absent")
    with pytest.raises(FileExistsError):
        write_report(out, {"purpose": "synthetic metadata"})
    assert not out.exists()
