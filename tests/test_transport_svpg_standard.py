"""Synthetic, bounded tests for the standard SVPG transport gate."""
import ast
import hashlib
import io
import json
from pathlib import Path
import threading
from types import SimpleNamespace
import zipfile

import pytest

pytest.importorskip("pysam")
from analysis import transport_svpg_standard as transport

REPO = Path(__file__).resolve().parents[1]
HEADER = (b"##fileformat=VCFv4.2\n##contig=<ID=chrSynthetic,length=10>\n"
          b'##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n'
          b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSample\n")


def vcf(pos0="0", posn="11", final_lf=False):
    rows = (f"chrSynthetic\t{pos0}\t.\tA\tC\t.\tPASS\t.\tGT\t0/1\n"
            f"chrSynthetic\t{posn}\t.\tA\tC\t.\tPASS\t.\tGT\t0/1")
    return HEADER + rows.encode() + (b"\n" if final_lf else b"")


class Meter:
    def __init__(self, wrapped):
        self.wrapped, self.total, self.requests = wrapped, 0, []
    def __enter__(self): return self
    def __exit__(self, *args): return self.wrapped.__exit__(*args)
    def __getattr__(self, name): return getattr(self.wrapped, name)
    def read(self, size=-1):
        self.requests.append(size)
        result = self.wrapped.read(size)
        self.total += len(result)
        return result


def test_copy_member_hash_newlines_crc_and_bounded_eof(tmp_path):
    raw, archive_path, output = vcf(), tmp_path / "synthetic.zip", io.BytesIO()
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_STORED) as archive:
        archive.writestr("member.vcf", raw)
    with zipfile.ZipFile(archive_path) as archive:
        stats = transport.copy_member(archive.open("member.vcf"), output, len(raw))
    assert output.getvalue() == raw
    assert stats == {"decoded_bytes": len(raw), "source_sha256": hashlib.sha256(raw).hexdigest(),
                     "newlines": raw.count(b"\n"), "last_byte_lf": False}

    for data, error, bound in ((raw[:-1], "truncated", len(raw)),
                               (raw + b"growth", "exceeds reservation", len(raw) + 1)):
        source, copied = Meter(io.BytesIO(data)), io.BytesIO()
        with pytest.raises(ValueError, match=error):
            transport.copy_member(source, copied, len(raw))
        assert source.total <= bound and all(0 < n <= 65536 for n in source.requests)


def test_copy_member_rejects_bad_zip_crc(tmp_path):
    raw, path, output = vcf(), tmp_path / "bad-crc.zip", io.BytesIO()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as archive:
        archive.writestr("member.vcf", raw)
    damaged = bytearray(path.read_bytes())
    offset = damaged.index(raw)
    damaged[offset + len(raw) // 2] ^= 1
    path.write_bytes(damaged)
    with zipfile.ZipFile(path) as archive, archive.open("member.vcf") as member:
        with pytest.raises(zipfile.BadZipFile):
            transport.copy_member(member, output, len(raw))


def test_standard_parser_counts_unclamped_boundary_positions(tmp_path):
    raw, path = vcf(), tmp_path / "synthetic.vcf"
    path.write_bytes(raw)
    report = transport.check_htslib(path, len(raw), hashlib.sha256(raw).hexdigest(),
                                    "Sample", [{"name": "chrSynthetic", "length": 10}])
    assert (report["records"], report["pos_zero"], report["pos_length_plus_one"]) == (2, 1, 1)
    assert report["compatibility_bytes_read"] == len(raw)
    assert report["positions_repaired"] == report["records_rewritten"] == report["records_filtered"] == 0


@pytest.mark.parametrize("pos", ["-1", "x"])
def test_standard_parser_rejects_invalid_positions(tmp_path, pos):
    raw, path = vcf(pos0=pos, posn="2"), tmp_path / "invalid.vcf"
    path.write_bytes(raw)
    with pytest.raises((ValueError, OSError)):
        transport.check_htslib(path, len(raw), hashlib.sha256(raw).hexdigest(), "Sample",
                               [{"name": "chrSynthetic", "length": 10}])


def test_parser_failure_stops_feeder_thread(tmp_path, monkeypatch):
    raw, path = vcf() * 20000, tmp_path / "large.vcf"
    path.write_bytes(raw)
    real_thread, workers = threading.Thread, []
    class TrackedThread(real_thread):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs); workers.append(self)
    monkeypatch.setattr(transport.threading, "Thread", TrackedThread)
    monkeypatch.setattr(transport.pysam, "VariantFile",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("synthetic parser failure")))
    with pytest.raises(Exception):
        transport.check_htslib(path, len(raw), hashlib.sha256(raw).hexdigest(),
                               "Sample", [{"name": "chrSynthetic", "length": 10}])
    assert len(workers) == 1 and not workers[0].is_alive()


def _case(tmp_path, header_bias=0):
    assert REPO not in tmp_path.resolve().parents
    raw, archive_path = vcf(), tmp_path / "six-synthetic.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for member in transport.MEMBERS:
            archive.writestr(member, raw)
    staged, completed = {}, {}
    with zipfile.ZipFile(archive_path) as archive:
        for caller, member in zip(transport.CALLERS[:4], transport.MEMBERS[:4]):
            info = archive.getinfo(member)
            path = tmp_path / f"{caller}.vcf"
            path.write_bytes(raw)
            digest = hashlib.sha256(raw).hexdigest()
            staged[caller] = {"staged_path": str(path), "staged_bytes": len(raw),
                              "staged_sha256": digest, "source_sha256": digest}
            completed[caller] = {"member": member, "decoded_bytes": len(raw),
                "selected_member_crc_verified": True, "crc32": f"{info.CRC:08x}",
                "staged_sha256": digest, "source_sha256": digest, "records": 2}
    report = tmp_path / "completed.json"
    report.write_text(json.dumps({"completed_callers": completed}))
    report_sha = hashlib.sha256(report.read_bytes()).hexdigest()
    for spec in staged.values():
        spec.update(report_path=str(report), report_sha256=report_sha)
    archive_bytes = archive_path.read_bytes()
    transport_bytes = 2 * len(raw)
    compatibility_bytes = 6 * len(raw)
    protocol = {"purpose": "transport_two_unfinished_v1", "body_read_approved": True,
        "independent_review": "synthetic", "pysam_version": transport.pysam.__version__,
        "local_samtools_version": transport.pysam.__samtools_version__,
        "members": list(transport.MEMBERS), "execution_callers": list(transport.CALLERS[-2:]),
        "reused_completed_callers": staged, "archive_bytes": len(archive_bytes),
        "archive_md5": hashlib.md5(archive_bytes).hexdigest(),
        "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "charged_prior_source_bytes": 0, "charged_prior_global_bytes": 0,
        "transport_reservation_bytes": transport_bytes + 2,
        "compatibility_reservation_bytes": compatibility_bytes,
        "source_limit_bytes": transport_bytes + 2,
        "global_limit_bytes": transport_bytes + compatibility_bytes + 2,
        "header_line_counts": {"svim": len(HEADER.splitlines()), "svpg": len(HEADER.splitlines()) + header_bias},
        "samples": {c: "Sample" for c in transport.CALLERS},
        "contigs": [{"name": "chrSynthetic", "length": 10}]}
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(protocol))
    return archive_path, protocol_path, hashlib.sha256(protocol_path.read_bytes()).hexdigest(), staged


@pytest.mark.parametrize("bias", [0, 1])
def test_transport_census_exactly_parses_reuse_once_and_keeps_failures(tmp_path, monkeypatch, bias):
    archive, protocol, pin, reused = _case(tmp_path, bias)
    monkeypatch.setattr(transport.os, "statvfs",
                        lambda _p: SimpleNamespace(f_bavail=10**15, f_frsize=1))
    targets = {Path(spec["staged_path"]).resolve() for spec in reused.values()}
    readers, original_open = [], Path.open
    def metered_open(path, *args, **kwargs):
        handle = original_open(path, *args, **kwargs)
        if Path(path).resolve() in targets and (args[:1] == ("rb",) or kwargs.get("mode") == "rb"):
            handle = Meter(handle)
            readers.append(handle)
        return handle
    monkeypatch.setattr(Path, "open", metered_open)
    outdir = tmp_path / "transport"
    if bias:
        with pytest.raises(ValueError, match="row census"):
            transport.run_transport(archive, outdir, protocol, pin)
        report = json.loads((outdir / "transport_report.json").read_text())
        assert report["status"] == "incomplete"
        assert all((outdir / f"{c}.vcf").read_bytes() == vcf() for c in transport.CALLERS[-2:])
    else:
        report = transport.run_transport(archive, outdir, protocol, pin)
        assert report["status"] == "complete"
        assert report["compatibility_reservation_bytes"] == 6 * len(vcf())
        assert all(report["compatibility"][c]["records"] == 2 for c in transport.CALLERS)
        for caller in transport.CALLERS[-2:]:
            assert (outdir / f"{caller}.vcf").read_bytes() == vcf()
            assert report["transported_callers"][caller]["selected_member_crc_verified"] is True
            assert report["transported_callers"][caller]["last_byte_lf"] is False
    assert len(readers) == 4
    assert all(r.total == len(vcf()) and all(0 < n <= 65536 for n in r.requests) for r in readers)


def test_protocol_sha_roster_and_no_import_autorun(tmp_path):
    path = tmp_path / "protocol.json"
    data = json.dumps({"purpose": "transport_two_unfinished_v1"}).encode()
    path.write_bytes(data)
    with pytest.raises(ValueError, match="SHA256"):
        transport.pinned_json(path, "0" * 64)
    protocol = {"purpose": "transport_two_unfinished_v1", "body_read_approved": True,
        "independent_review": "synthetic", "members": [],
        "execution_callers": list(transport.CALLERS[-2:]),
        "reused_completed_callers": {c: {} for c in transport.CALLERS[:4]}}
    path.write_text(json.dumps(protocol))
    with pytest.raises(ValueError, match="roster"):
        transport.run_transport(tmp_path / "absent.zip", tmp_path / "out",
                                path, hashlib.sha256(path.read_bytes()).hexdigest())
    tree = ast.parse(Path(transport.__file__).read_text())
    guard = tree.body[-1]
    assert isinstance(guard, ast.If) and "__name__" in ast.dump(guard.test)
    assert any(isinstance(n, ast.Call) and getattr(n.func, "id", None) == "run_transport"
               for n in ast.walk(guard))


@pytest.mark.parametrize("mutation", ["truncate", "grow", "read_failure", "digest"])
def test_compatibility_failed_inputs_bounded_and_thread_closed(tmp_path, monkeypatch, mutation):
    rows = vcf(final_lf=True)[len(HEADER):]
    raw, path = HEADER + rows * 5000, tmp_path / "input.vcf"
    path.write_bytes(raw)
    readers, workers = [], []
    original_open, real_thread = Path.open, threading.Thread
    class TrackedThread(real_thread):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            workers.append(self)
    class ChangedReader(Meter):
        def read(self, size=-1):
            if not self.requests:
                if mutation in ("truncate", "grow"):
                    with original_open(path, "wb") as output:
                        output.write(raw[:len(raw)//3] if mutation == "truncate" else raw + rows)
                if mutation == "read_failure":
                    self.requests.append(size)
                    raise OSError("synthetic feeder read error")
            return super().read(size)
    def open_input(p, *a, **k):
        handle = original_open(p, *a, **k)
        if p == path and a == ("rb",):
            handle = ChangedReader(handle)
            readers.append(handle)
        return handle
    monkeypatch.setattr(Path, "open", open_input)
    monkeypatch.setattr(transport.threading, "Thread", TrackedThread)
    digest = "0" * 64 if mutation == "digest" else hashlib.sha256(raw).hexdigest()
    with pytest.raises((ValueError, OSError)):
        transport.check_htslib(path, len(raw), digest, "Sample",
                               [{"name": "chrSynthetic", "length": 10}])
    assert len(workers) == 1 and not workers[0].is_alive()
    assert len(readers) == 1 and readers[0].total <= len(raw)
    assert all(0 < n <= 65536 for n in readers[0].requests)


@pytest.mark.parametrize("clock,expected", [("0:00.25", .25), ("12:03.50", 723.5),
                                            ("01:02:03", 3723), ("2-01:02:03", 176523)])
def test_cpu_clock(clock, expected):
    from scripts.run_svpg_standard_bounded import parse_cpu_time
    assert parse_cpu_time(clock) == expected


@pytest.mark.parametrize("clock", ["", "n/a", "0:nan", "1:60.1"])
def test_cpu_clock_invalid(clock):
    from scripts.run_svpg_standard_bounded import parse_cpu_time
    with pytest.raises(ValueError):
        parse_cpu_time(clock)


def test_library_pin_checked_before_archive_read(tmp_path):
    archive, protocol, _pin, _reused = _case(tmp_path)
    data = json.loads(protocol.read_text())
    data["local_samtools_version"] = "wrong"
    protocol.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="library version"):
        transport.run_transport(tmp_path / "absent.zip", tmp_path / "out", protocol,
                                hashlib.sha256(protocol.read_bytes()).hexdigest())


@pytest.mark.parametrize("clock", ["10:00.00", ""])
def test_runtime_cpu_sampler_stops_or_fails_closed(tmp_path, monkeypatch, clock):
    from scripts import run_svpg_standard_bounded as launcher
    logdir = tmp_path / "logs"
    monkeypatch.setattr(launcher.sys, "argv", ["synthetic", "--archive", "none", "--outdir", str(tmp_path / "out"),
                       "--protocol", "none", "--protocol-sha256", "0" * 64, "--logdir", str(logdir)])
    monkeypatch.setattr(launcher.resource, "setrlimit", lambda *a: None)
    monkeypatch.setattr(launcher.resource, "getrusage", lambda _which: SimpleNamespace(ru_utime=0, ru_stime=0))
    monkeypatch.setattr(launcher.bounded, "sample_process", lambda _pid: (1000, []))
    monkeypatch.setattr(launcher.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout=clock))
    monkeypatch.setattr(launcher.bounded, "CPU_SECONDS", 1800)
    def fake_bounded(_command, directory, *, sampler, wall_seconds):
        assert wall_seconds == 900 and launcher.bounded.CPU_SECONDS == 550
        if clock:
            with pytest.raises(RuntimeError, match="CPU"):
                sampler(999)
        else:
            # The existing supervisor fails closed on RSS=0 while child live.
            assert sampler(999) == (0, [])
        directory.mkdir()
        return {"status": "incomplete", "combined_cpu_seconds": 1}
    monkeypatch.setattr(launcher.bounded, "run_bounded", fake_bounded)
    with pytest.raises(SystemExit):
        launcher.main()
    guard = json.loads((logdir / "cpu_guard.json").read_text())
    assert guard["budget_pass"] is False and guard["sampled_combined_cpu_stop_seconds"] == 580


def test_actual_guard_launches_child_with_real_cpu_limits(tmp_path, monkeypatch):
    import sys
    from scripts import run_svpg_standard_bounded as launcher
    # Restore the old module constant after this test; no parent's limits change.
    monkeypatch.setattr(launcher.bounded, "CPU_SECONDS", 1800)
    program = ("import resource,time,json; "
               "limits=resource.getrlimit(resource.RLIMIT_CPU); "
               "assert limits==(550,550),limits; "
               "print(json.dumps({'synthetic':True,'child_cpu_limits':limits}),flush=True); "
               "time.sleep(0.3)")
    result = launcher.run_with_guard([sys.executable, "-c", program], tmp_path / "real-guard")
    assert result["resources"]["status"] == "complete"
    assert result["cpu_guard"]["budget_pass"] is True
    assert result["resources"]["child_cpu_limit_seconds"] == 550
    output = json.loads((tmp_path / "real-guard/stdout.log").read_text())
    assert output == {"synthetic": True, "child_cpu_limits": [550, 550]}
