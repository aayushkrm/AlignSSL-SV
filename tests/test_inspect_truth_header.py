import gzip
import hashlib
import json
import zlib

import pytest

from analysis.inspect_truth_header import inspect_header

HEADER = (b'##fileformat=VCFv4.2\n##contig=<ID=1,length=100>\n'
          b'##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n'
          b'#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tEXACT\n')


def run(path, raw, **kwargs):
    path.write_bytes(raw)
    return inspect_header(path, len(raw), hashlib.sha256(raw).hexdigest(), **kwargs)


def test_header_only_and_read_ahead_cap(tmp_path):
    raw = gzip.compress(HEADER + b'1\t1\tNOT_SAVED\t' + b'A' * (3 * 1024**2), mtime=0)
    report = run(tmp_path / 'truth.gz', raw)
    assert report['samples'] == ['EXACT']
    assert report['header_sha256'] == hashlib.sha256(HEADER).hexdigest()
    assert report['decoded_prefix_bytes_including_read_ahead'] == 1024**2
    assert report['body_records_parsed'] == report['body_records_saved'] == 0
    assert 'NOT_SAVED' not in json.dumps(report)
    assert not report['first_gzip_member_eof_crc_verified']


def test_concatenated_gzip_first_member_only(tmp_path):
    first = gzip.compress(HEADER + b'1\t0\tUNSEEN\n', mtime=0)
    raw = first + gzip.compress(b'OTHER_UNSEEN_BODY\n', mtime=0)
    report = run(tmp_path / 'truth.gz', raw)
    assert report['first_gzip_member_eof_crc_verified']
    assert report['decoded_prefix_bytes_including_read_ahead'] == len(HEADER) + len(b'1\t0\tUNSEEN\n')
    assert not report['whole_gzip_crc_verified']
    assert 'UNSEEN' not in json.dumps(report)


@pytest.mark.parametrize('payload', [b'##fileformat=VCFv4.2\n', HEADER[:-1], b'1\t2\tBODY\n'])
def test_incomplete_or_nonheader_fails_no_retry(tmp_path, payload):
    with pytest.raises(ValueError):
        run(tmp_path / 'truth.gz', gzip.compress(payload, mtime=0))


def test_full_hash_before_decode(tmp_path):
    path = tmp_path / 'truth.gz'
    raw = gzip.compress(HEADER, mtime=0)
    path.write_bytes(raw)
    with pytest.raises(ValueError, match='SHA'):
        inspect_header(path, len(raw), '0' * 64)
    with pytest.raises(ValueError, match='size'):
        inspect_header(path, len(raw) + 1, hashlib.sha256(raw).hexdigest())


def test_first_member_bad_crc(tmp_path):
    raw = bytearray(gzip.compress(HEADER, mtime=0))
    raw[-8] ^= 1
    with pytest.raises(zlib.error):
        run(tmp_path / 'truth.gz', bytes(raw))


def test_limit_before_header(tmp_path):
    with pytest.raises(ValueError):
        run(tmp_path / 'truth.gz', gzip.compress(HEADER, mtime=0), decoded_cap=20)


def test_growth_during_prefix_read_rejected_with_bounded_reads(tmp_path, monkeypatch):
    from pathlib import Path
    path = tmp_path / 'truth.gz'
    raw = gzip.compress(HEADER + b'1\t0\tUNSEEN\n', mtime=0)
    path.write_bytes(raw)
    original_open, reads = Path.open, []
    class Growing:
        def __init__(self, source): self.source = source
        def __enter__(self): return self
        def __exit__(self, *a): return self.source.__exit__(*a)
        def __getattr__(self, name): return getattr(self.source, name)
        def read(self, size):
            reads.append(size)
            if len(reads) == 2:
                with original_open(path, 'ab') as output: output.write(b'growth')
            return self.source.read(size)
    def tracked(p, *a, **k):
        result = original_open(p, *a, **k)
        return Growing(result) if p == path and a == ('rb',) else result
    monkeypatch.setattr(Path, 'open', tracked)
    with pytest.raises(ValueError, match='changed'):
        inspect_header(path, len(raw), hashlib.sha256(raw).hexdigest())
    assert reads == [len(raw), len(raw)]
