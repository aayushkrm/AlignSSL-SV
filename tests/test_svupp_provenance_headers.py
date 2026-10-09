"""Synthetic controls for the bounded SVUPP provenance/header reader."""

import errno
import gzip
import hashlib
import json
import os
import struct
import zipfile

import pytest

import analysis.inspect_svupp_provenance_headers as inspector


FIXED_SPECS = dict(inspector.MEMBER_SPECS)
TEXT_NAMES = [name for name, (kind, _size) in FIXED_SPECS.items() if kind == "text"]
GZIP_NAMES = [name for name, (kind, _size) in FIXED_SPECS.items() if kind == "gzip_vcf"]


def _vcf_header(*samples):
    columns = b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"
    if samples:
        columns += b"\tFORMAT" + b"".join(b"\t" + sample for sample in samples)
    return b"##fileformat=VCFv4.2\n" + columns + b"\n"


def _body_sentinel():
    return b"1\t42\tBODY_SENTINEL_DO_NOT_EXPORT\tA\tC\t.\tPASS\t.\tGT\t0/1\n" + b"x" * (80 * 1024)


def _fixture_payloads():
    text = {
        TEXT_NAMES[0]: "# Synthetic README\nAuthor text is provenance only.\n".encode(),
        TEXT_NAMES[1]: "sample,technology,depth\nS1,ONT_UL,30x\n".encode(),
        TEXT_NAMES[2]: "workflow {\n  // not executed\n}\n".encode(),
        TEXT_NAMES[3]: "# no-neighbors analysis source\n".encode(),
        TEXT_NAMES[4]: "# with-neighbors analysis source\n".encode(),
    }
    gzipped = {
        GZIP_NAMES[0]: gzip.compress(_vcf_header(b"PLATINUM") + _body_sentinel(), mtime=0),
        GZIP_NAMES[1]: gzip.compress(_vcf_header() + _body_sentinel(), mtime=0),
        GZIP_NAMES[2]: gzip.compress(_vcf_header(b"SAMPLE_A", b"SAMPLE_B") + _body_sentinel(), mtime=0),
    }
    return {**text, **gzipped}


def _install_fixture_specs(monkeypatch, payloads):
    specs = {name: (FIXED_SPECS[name][0], len(payload)) for name, payload in payloads.items()}
    monkeypatch.setattr(inspector, "MEMBER_SPECS", specs)


def _write_archive(path, payloads, monkeypatch):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        for name, payload in payloads.items():
            archive.writestr(name, payload)
    with zipfile.ZipFile(path, "r") as archive:
        compressed_bytes = sum(info.compress_size for info in archive.infolist())
    monkeypatch.setattr(inspector, "EXPECTED_SELECTED_COMPRESSED_BYTES", compressed_bytes)
    return path


def _pins(path):
    data = path.read_bytes()
    return {
        "expected_bytes": len(data),
        "expected_md5": hashlib.md5(data).hexdigest(),
        "expected_sha256": hashlib.sha256(data).hexdigest(),
    }


def _inspect(path, output, **overrides):
    pins = _pins(path)
    pins.update(overrides)
    return inspector.inspect_provenance_headers(path, output_manifest=output, **pins)


def _make_fixture(tmp_path, monkeypatch):
    payloads = _fixture_payloads()
    _install_fixture_specs(monkeypatch, payloads)
    source = _write_archive(tmp_path / "synthetic.zip", payloads, monkeypatch)
    return source, payloads


def test_fixed_member_map_matches_the_protocol():
    assert FIXED_SPECS == {
        "SVUPP_paper/README.md": ("text", 2_835),
        "SVUPP_paper/samplesheet/platinum-ont-ul.csv": ("text", 1_568),
        "SVUPP_paper/pipeline/bench-force-calling.nf": ("text", 6_496),
        "SVUPP_paper/reproduceplot/discordance_per_GQ_noneighbors.R": ("text", 5_329),
        "SVUPP_paper/reproduceplot/discordance_per_GQ_withneighbors.R": ("text", 5_346),
        "SVUPP_paper/reproduceplot/platinum.withdist1000.vcf.gz": ("gzip_vcf", 9_222_119),
        "SVUPP_paper/reproduceplot/kanpig.vcf.gz": ("gzip_vcf", 10_950_303),
        "SVUPP_paper/reproduceplot/svupp.vcf.gz": ("gzip_vcf", 9_250_146),
    }
    assert inspector.EXPECTED_SELECTED_COMPRESSED_BYTES == 28_409_706


def test_complete_eight_member_read_preserves_provenance_and_headers(tmp_path, monkeypatch):
    source, payloads = _make_fixture(tmp_path, monkeypatch)
    output = tmp_path / "provenance.json"
    original_pread = inspector.os.pread
    source_reads = []

    def track_pread(fd, amount, offset):
        block = original_pread(fd, amount, offset)
        source_reads.append((offset, amount, len(block)))
        return block

    monkeypatch.setattr(inspector.os, "pread", track_pread)
    report = _inspect(source, output)

    assert report["inspection_status"] == "COMPLETE_BOUNDED_PROVENANCE_HEADERS"
    assert report["source_archive_full_opaque_hash_passes"] == 2
    assert [(offset, amount, read) for offset, amount, read in source_reads] == [
        (0, source.stat().st_size, source.stat().st_size),
        (0, source.stat().st_size, source.stat().st_size),
    ]
    assert report["fixed_member_count"] == 8
    assert report["all_selected_outer_zip_members_read_to_crc_eof"] is True
    assert report["author_text_executed"] is False
    assert report["bodies_decoded"] is True
    assert report["genotype_records_not_interpreted"] is True
    assert report["nested_gzip_full_crc_not_assessed"] is True
    assert report["gzip_read_ahead_may_include_body_bytes"] is True
    assert report["usable_data_readiness_assessed"] is False
    assert "outcomes_not_read" not in report

    by_name = {member["name"]: member for member in report["members"]}
    with zipfile.ZipFile(source, "r") as archive:
        infos = {info.filename: info for info in archive.infolist()}
    assert report["selected_outer_zip_compressed_bytes"] == sum(
        infos[name].compress_size for name in FIXED_SPECS
    )
    for name, info in infos.items():
        member = by_name[name]
        assert member["outer_zip_declared_uncompressed_bytes"] == info.file_size
        assert member["outer_zip_compressed_bytes"] == info.compress_size
        assert member["outer_zip_crc32"] == f"{info.CRC:08x}"
    for name in TEXT_NAMES:
        assert by_name[name]["text_utf8"] == payloads[name].decode("utf-8")
        assert by_name[name]["author_text_executed"] is False
        assert by_name[name]["member_sha256"] == hashlib.sha256(payloads[name]).hexdigest()
    for name in GZIP_NAMES:
        member = by_name[name]
        assert member["member_sha256"] == hashlib.sha256(payloads[name]).hexdigest()
        assert member["outer_zip_crc_verified_by_complete_read"] is True
        assert member["nested_gzip_full_crc_not_assessed"] is True
        assert member["genotype_records_not_interpreted"] is True
        assert member["body_bytes_may_be_included_by_gzip_read_ahead"] is True
    assert by_name[GZIP_NAMES[0]]["sample_names"] == ["PLATINUM"]
    assert by_name[GZIP_NAMES[1]]["sample_names"] == []
    assert by_name[GZIP_NAMES[1]]["genotyping_input_status"] == "missing_sample_columns"
    assert by_name[GZIP_NAMES[2]]["sample_names"] == ["SAMPLE_A", "SAMPLE_B"]

    serialized = output.read_text(encoding="utf-8")
    assert "BODY_SENTINEL_DO_NOT_EXPORT" not in serialized
    assert output.stat().st_size <= 1024 * 1024
    assert json.loads(serialized) == report


def test_sites_only_eight_column_header_is_valid_and_marks_missing_inputs(tmp_path, monkeypatch):
    payloads = _fixture_payloads()
    payloads[GZIP_NAMES[0]] = gzip.compress(_vcf_header() + _body_sentinel(), mtime=0)
    _install_fixture_specs(monkeypatch, payloads)
    source = _write_archive(tmp_path / "sites-only.zip", payloads, monkeypatch)

    report = _inspect(source, tmp_path / "sites-only.json")

    member = {entry["name"]: entry for entry in report["members"]}[GZIP_NAMES[0]]
    assert member["vcf_columns"] == "#CHROM POS ID REF ALT QUAL FILTER INFO".split()
    assert member["sample_names"] == []
    assert member["format_column_present"] is False
    assert member["genotyping_input_status"] == "missing_sample_columns"


def test_format_column_without_samples_is_rejected(tmp_path, monkeypatch):
    payloads = _fixture_payloads()
    payloads[GZIP_NAMES[0]] = gzip.compress(_vcf_header()[:-1] + b"\tFORMAT\n" + _body_sentinel(), mtime=0)
    _install_fixture_specs(monkeypatch, payloads)
    source = _write_archive(tmp_path / "format-no-samples.zip", payloads, monkeypatch)

    with pytest.raises(ValueError, match="FORMAT column has no sample"):
        _inspect(source, tmp_path / "format-no-samples.json")


def test_header_at_exact_256_kib_limit_is_accepted(tmp_path, monkeypatch):
    payloads = _fixture_payloads()
    prefix = b"##fileformat=VCFv4.2\n##padding="
    columns = b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
    padding = b"x" * (inspector.MAX_VCF_HEADER_BYTES - len(prefix) - len(columns) - 1)
    header = prefix + padding + b"\n" + columns
    assert len(header) == inspector.MAX_VCF_HEADER_BYTES
    payloads[GZIP_NAMES[0]] = gzip.compress(header + _body_sentinel(), mtime=0)
    _install_fixture_specs(monkeypatch, payloads)
    source = _write_archive(tmp_path / "exact-header-limit.zip", payloads, monkeypatch)

    report = _inspect(source, tmp_path / "exact-header-limit.json")

    member = {entry["name"]: entry for entry in report["members"]}[GZIP_NAMES[0]]
    assert member["vcf_header_bytes"] == inspector.MAX_VCF_HEADER_BYTES
    assert member["vcf_header_text"].encode("utf-8") == header


def test_header_beyond_256_kib_limit_is_rejected(tmp_path, monkeypatch):
    payloads = _fixture_payloads()
    prefix = b"##fileformat=VCFv4.2\n##padding="
    columns = b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
    padding = b"x" * (inspector.MAX_VCF_HEADER_BYTES - len(prefix) - len(columns))
    payloads[GZIP_NAMES[0]] = gzip.compress(prefix + padding + b"\n" + columns + _body_sentinel(), mtime=0)
    _install_fixture_specs(monkeypatch, payloads)
    source = _write_archive(tmp_path / "over-header-limit.zip", payloads, monkeypatch)

    with pytest.raises(ValueError, match="256 KiB"):
        _inspect(source, tmp_path / "over-header-limit.json")


@pytest.mark.parametrize(
    "header, message",
    [
        (b"##fileformat=VCFv4.2\n1\t1\tRECORD_BEFORE_CHROM\n", "before #CHROM"),
        (b"##fileformat=VCFv4.2\n#CHROM\tPOS\tBAD\n", "fixed-column prefix"),
        (_vcf_header(b"DUP", b"DUP"), "sample names must be unique"),
    ],
)
def test_missing_or_invalid_header_fails_without_report(tmp_path, monkeypatch, header, message):
    payloads = _fixture_payloads()
    payloads[GZIP_NAMES[0]] = gzip.compress(header + _body_sentinel(), mtime=0)
    _install_fixture_specs(monkeypatch, payloads)
    source = _write_archive(tmp_path / "invalid-header.zip", payloads, monkeypatch)
    output = tmp_path / "invalid-header.json"

    with pytest.raises(ValueError, match=message):
        _inspect(source, output)
    assert not output.exists()


def test_eof_before_chrom_is_rejected(tmp_path, monkeypatch):
    payloads = _fixture_payloads()
    payloads[GZIP_NAMES[0]] = gzip.compress(b"##fileformat=VCFv4.2\n", mtime=0)
    _install_fixture_specs(monkeypatch, payloads)
    source = _write_archive(tmp_path / "eof-before-chrom.zip", payloads, monkeypatch)

    with pytest.raises(ValueError, match="#CHROM header is absent"):
        _inspect(source, tmp_path / "eof-before-chrom.json")


def test_invalid_nested_gzip_stops_without_report(tmp_path, monkeypatch):
    payloads = _fixture_payloads()
    payloads[GZIP_NAMES[0]] = b"not a gzip member"
    _install_fixture_specs(monkeypatch, payloads)
    source = _write_archive(tmp_path / "invalid-gzip.zip", payloads, monkeypatch)

    with pytest.raises((gzip.BadGzipFile, EOFError, OSError)):
        _inspect(source, tmp_path / "invalid-gzip.json")


def test_text_member_requires_strict_utf8(tmp_path, monkeypatch):
    payloads = _fixture_payloads()
    payloads[TEXT_NAMES[0]] = b"invalid UTF-8: \xff"
    _install_fixture_specs(monkeypatch, payloads)
    source = _write_archive(tmp_path / "invalid-text-utf8.zip", payloads, monkeypatch)

    with pytest.raises(UnicodeDecodeError):
        _inspect(source, tmp_path / "invalid-text-utf8.json")


def test_vcf_header_requires_strict_utf8(tmp_path, monkeypatch):
    payloads = _fixture_payloads()
    payloads[GZIP_NAMES[0]] = gzip.compress(
        b"##metadata=\xff\n" + _vcf_header(b"SAMPLE") + _body_sentinel(), mtime=0,
    )
    _install_fixture_specs(monkeypatch, payloads)
    source = _write_archive(tmp_path / "invalid-header-utf8.zip", payloads, monkeypatch)

    with pytest.raises(UnicodeDecodeError):
        _inspect(source, tmp_path / "invalid-header-utf8.json")


def test_wrong_source_hash_and_size_stop_before_report(tmp_path, monkeypatch):
    source, _payloads = _make_fixture(tmp_path, monkeypatch)
    pins = _pins(source)
    output = tmp_path / "wrong-pins.json"

    with pytest.raises(ValueError, match="MD5 or SHA256"):
        inspector.inspect_provenance_headers(
            source, output_manifest=output, **{**pins, "expected_sha256": "0" * 64},
        )
    with pytest.raises(ValueError, match="size differs"):
        inspector.inspect_provenance_headers(
            source, output_manifest=output, **{**pins, "expected_bytes": pins["expected_bytes"] + 1},
        )
    assert not output.exists()


def test_wrong_md5_stops_before_report(tmp_path, monkeypatch):
    source, _payloads = _make_fixture(tmp_path, monkeypatch)
    pins = _pins(source)

    with pytest.raises(ValueError, match="MD5 or SHA256"):
        inspector.inspect_provenance_headers(
            source, output_manifest=tmp_path / "wrong-md5.json",
            **{**pins, "expected_md5": "0" * 32},
        )


def test_source_mutation_during_member_read_is_rejected(tmp_path, monkeypatch):
    source, _payloads = _make_fixture(tmp_path, monkeypatch)
    original = inspector._read_complete_member
    mutated = False

    def mutate_after_read(archive, info, expected_size):
        nonlocal mutated
        result = original(archive, info, expected_size)
        if not mutated:
            with source.open("r+b") as handle:
                handle.seek(0)
                handle.write(b"X")
                handle.flush()
                os.fsync(handle.fileno())
            mutated = True
        return result

    monkeypatch.setattr(inspector, "_read_complete_member", mutate_after_read)
    with pytest.raises(ValueError, match="changed during inspection"):
        _inspect(source, tmp_path / "mutated.json")
    assert not (tmp_path / "mutated.json").exists()


def test_outer_zip_crc_corruption_is_rejected(tmp_path, monkeypatch):
    source, payloads = _make_fixture(tmp_path, monkeypatch)
    damaged = bytearray(source.read_bytes())
    target = TEXT_NAMES[0].encode("utf-8")
    cursor = 0
    while True:
        central = damaged.find(b"PK\x01\x02", cursor)
        if central < 0:
            raise AssertionError("synthetic ZIP central entry not found")
        name_length = struct.unpack_from("<H", damaged, central + 28)[0]
        extra_length = struct.unpack_from("<H", damaged, central + 30)[0]
        comment_length = struct.unpack_from("<H", damaged, central + 32)[0]
        name_start = central + 46
        if bytes(damaged[name_start:name_start + name_length]) == target:
            crc = struct.unpack_from("<I", damaged, central + 16)[0]
            struct.pack_into("<I", damaged, central + 16, crc ^ 1)
            break
        cursor = name_start + name_length + extra_length + comment_length
    source.write_bytes(damaged)

    with pytest.raises(zipfile.BadZipFile, match="Bad CRC"):
        _inspect(source, tmp_path / "bad-crc.json")


def test_missing_fixed_member_and_declared_size_mismatch_stop(tmp_path, monkeypatch):
    payloads = _fixture_payloads()
    _install_fixture_specs(monkeypatch, payloads)
    missing = dict(payloads)
    missing.pop(TEXT_NAMES[-1])
    missing_source = _write_archive(tmp_path / "missing-member.zip", missing, monkeypatch)
    with pytest.raises(ValueError, match="missing or duplicated"):
        _inspect(missing_source, tmp_path / "missing-member.json")

    wrong_size = dict(payloads)
    wrong_size[TEXT_NAMES[0]] += b"x"
    size_source = _write_archive(tmp_path / "wrong-member-size.zip", wrong_size, monkeypatch)
    with pytest.raises(ValueError, match="size differs from the declaration"):
        _inspect(size_source, tmp_path / "wrong-member-size.json")


def test_existing_manifest_is_never_overwritten(tmp_path, monkeypatch):
    source, _payloads = _make_fixture(tmp_path, monkeypatch)
    output = tmp_path / "existing.json"
    output.write_bytes(b"keep this report\n")

    with pytest.raises(FileExistsError):
        _inspect(source, output)
    assert output.read_bytes() == b"keep this report\n"


def test_source_symlink_hardlink_and_symlink_parent_are_rejected(tmp_path, monkeypatch):
    source, _payloads = _make_fixture(tmp_path, monkeypatch)
    pins = _pins(source)

    symbolic = tmp_path / "symbolic.zip"
    try:
        symbolic.symlink_to(source)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")
    with pytest.raises(ValueError, match="regular, non-link, single-link"):
        inspector.inspect_provenance_headers(
            symbolic, output_manifest=tmp_path / "symbolic.json", **pins,
        )

    hardlinked = tmp_path / "hardlinked.zip"
    try:
        os.link(source, hardlinked)
    except OSError as exc:
        pytest.skip(f"hardlink creation is unavailable: {exc}")
    with pytest.raises(ValueError, match="regular, non-link, single-link"):
        inspector.inspect_provenance_headers(
            hardlinked, output_manifest=tmp_path / "hardlinked.json", **pins,
        )

    linked_parent = tmp_path / "linked-parent"
    try:
        linked_parent.symlink_to(tmp_path, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlink creation is unavailable: {exc}")
    with pytest.raises(ValueError, match="parent.*symlink") as raised:
        inspector.inspect_provenance_headers(
            linked_parent / source.name,
            output_manifest=tmp_path / "parent-link.json",
            **pins,
        )
    assert isinstance(raised.value.__cause__, OSError)
    assert raised.value.__cause__.filename == linked_parent.name
    assert raised.value.__cause__.errno in (errno.ELOOP, errno.ENOTDIR)


def test_manifest_writer_enforces_one_mib_cap(tmp_path, monkeypatch):
    source, _payloads = _make_fixture(tmp_path, monkeypatch)
    import analysis.inspect_pinned_research_zip as source_guards

    monkeypatch.setattr(source_guards, "MAX_MANIFEST_BYTES", 16)
    output = tmp_path / "too-large-report.json"
    with pytest.raises(ValueError, match="manifest exceeds"):
        _inspect(source, output)
    assert not output.exists()


def test_combined_json_escaping_hits_real_one_mib_cap_without_partial_report(
    tmp_path, monkeypatch,
):
    payloads = _fixture_payloads()
    prefix = b"##fileformat=VCFv4.2\n##padding="
    columns = b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
    room = inspector.MAX_VCF_HEADER_BYTES - len(prefix) - len(columns) - 1
    padding = "é".encode("utf-8") * (room // 2) + b"x" * (room % 2)
    header = prefix + padding + b"\n" + columns
    assert len(header) == inspector.MAX_VCF_HEADER_BYTES
    for name in GZIP_NAMES:
        payloads[name] = gzip.compress(header + _body_sentinel(), mtime=0)
    _install_fixture_specs(monkeypatch, payloads)
    source = _write_archive(tmp_path / "escaped-report-cap.zip", payloads, monkeypatch)
    output = tmp_path / "escaped-report-cap.json"

    with pytest.raises(ValueError, match="manifest exceeds"):
        _inspect(source, output)

    assert not output.exists()
    assert source.stat().st_size < 2 * 1024**2
