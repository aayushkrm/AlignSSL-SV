"""Controls for the case-only BND reference-name diagnostic."""
import pytest

from analysis.colo829_contig_alias_diagnostic import normalized_copy


def source(headers, alt=b'A[CHR2:200[', info=b'SVTYPE=BND;ANN=CHR2'):
    return (b'##fileformat=VCFv4.3\n' + headers +
            b'#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n' +
            b'chr1\t100\ta\tA\t' + alt + b'\t.\tPASS\t' + info + b'\n')


def test_only_remote_alt_token_changes():
    data = source(b'##contig=<ID=chr1,length=500>\n##contig=<ID=chr2,length=500>\n')
    revised, counts, changes = normalized_copy(data)
    assert revised == data.replace(b'A[CHR2:200[', b'A[chr2:200[')
    assert b'ANN=CHR2' in revised
    assert counts['case_only_changes'] == 1 and len(changes) == 1


def test_exact_name_is_not_modified():
    data = source(b'##contig=<ID=chr2,length=500>\n', alt=b'A[chr2:200[')
    revised, counts, _ = normalized_copy(data)
    assert revised == data
    assert counts['already_exact'] == 1


def test_unresolvable_or_ambiguous_alias_fails():
    with pytest.raises(ValueError, match='no unique case-only alias'):
        normalized_copy(source(b'##contig=<ID=chr3,length=500>\n'))
    with pytest.raises(ValueError, match='no unique case-only alias'):
        normalized_copy(source(b'##contig=<ID=chr2,length=500>\n##contig=<ID=CHR2,length=500>\n'))


def test_multiallelic_bnd_is_not_silently_rewritten():
    with pytest.raises(ValueError, match='unsupported or multiple'):
        normalized_copy(source(b'##contig=<ID=chr2,length=500>\n',
                               alt=b'A[CHR2:200[,A[CHR2:201['))
