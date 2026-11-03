"""Observable controls for BND parsing and conservative reciprocal pairing."""
from pathlib import Path

import pytest

from analysis.colo829_bnd_anchor_census import census, pair_records, parse_bnd


def row(chrom, pos, ident, ref, alt, mate=None):
    info = 'SVTYPE=BND' + (f';MATEID={mate}' if mate else '')
    return [chrom, str(pos), ident, ref, alt, '.', 'PASS', info]


@pytest.mark.parametrize('alt_a,alt_b', [
    ('A]chr2:200]', 'C]chr1:100]'),
    ('A[chr2:200[', ']chr1:100]C'),
    (']chr2:200]A', 'C[chr1:100['),
    ('[chr2:200[A', '[chr1:100[C'),
])
def test_all_four_reciprocal_orientations(alt_a, alt_b):
    records = [parse_bnd(row('chr1', 100, 'a', 'A', alt_a, 'b')),
               parse_bnd(row('chr2', 200, 'b', 'C', alt_b, 'a'))]
    pair_records(records)
    assert [x['mate_status'] for x in records] == ['UNIQUE_RECIPROCAL'] * 2
    assert all(x['anchor_matches_local_ref'] for x in records)


def test_different_anchor_is_recorded_without_calling_it_an_error():
    records = [parse_bnd(row('chr1', 100, 'a', 'A', 'C[chr2:200[', 'b')),
               parse_bnd(row('chr2', 200, 'b', 'C', ']chr1:100]C', 'a'))]
    pair_records(records)
    assert not records[0]['anchor_matches_local_ref']
    assert records[0]['anchor_matches_reciprocal_ref']
    assert records[0]['mate_status'] == 'UNIQUE_RECIPROCAL'


def test_missing_and_ambiguous_reciprocals_remain_unknown():
    a = parse_bnd(row('chr1', 100, 'a', 'A', 'A[chr2:200['))
    pair_records([a])
    assert a['mate_status'] == 'UNKNOWN_NO_RECIPROCAL_RECORD'
    b = parse_bnd(row('chr2', 200, 'b', 'C', ']chr1:100]C'))
    c = parse_bnd(row('chr2', 200, 'c', 'C', ']chr1:100]C'))
    pair_records([a, b, c])
    assert a['mate_status'] == 'UNKNOWN_MULTIPLE_RECIPROCAL_RECORDS'
    assert b['mate_status'] == c['mate_status'] == 'UNKNOWN_ASYMMETRIC_PAIRING'


def test_multiallelic_and_symbolic_alts_are_unknown():
    records = [parse_bnd(row('1', 100, 'a', 'A', 'A[2:200[,A[3:300[')),
               parse_bnd(row('1', 101, 'b', 'C', '<BND>'))]
    pair_records(records)
    assert all(x['parse_status'] == 'UNKNOWN_ALT_REPRESENTATION' for x in records)
    assert all(x['mate_status'] == 'UNKNOWN_UNPARSED' for x in records)


def test_whole_file_denominator_and_sample_are_retained(tmp_path: Path):
    p = tmp_path / 'fixture.vcf'
    p.write_text('##fileformat=VCFv4.3\n##reference=synthetic\n'
                 '#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n'
                 '1\t100\ta\tA\tC[chr2:200[\t.\tPASS\tSVTYPE=BND;MATEID=b\tGT\t0/1\n'
                 '2\t200\tb\tC\t]chr1:100]C\t.\tPASS\tSVTYPE=BND;MATEID=a\tGT\t0/1\n'
                 '1\t300\tc\tA\t<DEL>\t.\tPASS\tSVTYPE=DEL\tGT\t0/1\n')
    result = census(p)
    assert result['sample_names'] == ['SAMPLE']
    assert result['reference_headers'] == ['synthetic']
    assert result['all_record_svtypes'] == {'BND': 2, 'DEL': 1}
    assert result['counts']['UNIQUE_RECIPROCAL'] == 2
    assert result['counts']['different_local_anchor_equals_mate_ref'] == 1
