"""Identity and file reconciliation controls for the frozen public metadata."""
import csv
from pathlib import Path
import shutil

import pytest

from analysis.synvii_archive_inventory import EXPERIMENT, LINKS, SAMPLE, TABLE, inventory, main

SOURCE = Path(__file__).resolve().parents[1] / 'results/synvii_archive_inventory_20261103'


@pytest.fixture
def packet(tmp_path):
    for name in (SAMPLE, EXPERIMENT, LINKS, TABLE):
        shutil.copyfile(SOURCE / name, tmp_path / name)
    return tmp_path


def change_row(path, edit):
    with path.open(newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        fields, rows = reader.fieldnames, list(reader)
    edit(rows)
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fields, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)


def test_actual_packet_retains_unmatched_and_ambiguous_records():
    d = inventory(SOURCE)
    assert d['counts'] == dict(samples=231, experiments=292, runs=319, raw_file_links=638,
                              reference_sequence_links=2, source_strains=127)
    assert d['strategies'] == {'WGS': 230, 'Hi-C': 12, 'RNA-Seq': 77}
    assert d['alias_status_counts'] == dict(EXACT=67, NO_SOURCE_STRAIN_ROW=160,
                                          UNSPECIFIED_SOURCE_ALIAS=1, TEXT_MISMATCH=3)
    assert len(d['source_strains_without_archive_sample']) == 56
    assert len(d['samples']) == 231
    mismatches = {s['sample']['sample_name'] for s in d['samples'] if s['alias_status']=='TEXT_MISMATCH'}
    assert mismatches == {'YSy105', 'YSy142', 'YSy140'}
    assert d['sources'][TABLE]['sha256'] == 'b7fcd9867096dcd52f6e551c28287c9f2c8d9c0a46236c1a53fc6524803ed3c5'


@pytest.mark.parametrize('name,edit,error', [
    (SAMPLE, lambda r: r.append(r[0].copy()), 'duplicate sample accession'),
    (EXPERIMENT, lambda r: r.append(r[0].copy()), 'duplicate run accession'),
    (EXPERIMENT, lambda r: r[0].update(project_accession='CNP0000000'), 'foreign project'),
    (EXPERIMENT, lambda r: r[0].update(sample_name='wrong'), 'sample identity mismatch'),
    (EXPERIMENT, lambda r: r[0].update(file_md5='invalid'), 'invalid declared MD5'),
    (EXPERIMENT, lambda r: r[0].update(file_md5=''), 'unpaired filename/checksum'),
])
def test_invalid_identity_and_files_fail_closed(packet, name, edit, error):
    change_row(packet / name, edit)
    with pytest.raises(ValueError, match=error):
        inventory(packet)


@pytest.mark.parametrize('mutation,error', [
    (lambda lines: lines[:-1], 'manifest/metadata file mismatch'),
    (lambda lines: lines+[lines[-1]], 'duplicate manifest file'),
    (lambda lines: lines+['experiment ftp://example.org/extra.fq.gz'], 'manifest/metadata file mismatch'),
])
def test_manifest_disagreement_rejected(packet, mutation, error):
    p = packet / LINKS
    p.write_text('\n'.join(mutation(p.read_text().splitlines()))+'\n')
    with pytest.raises(ValueError, match=error):
        inventory(packet)


def test_alias_disagreement_is_visible_not_repaired(packet):
    def edit(rows):
        next(r for r in rows if r['sample_name']=='YSy150')['isolate'] = 'F2-93 '
    change_row(packet / SAMPLE, edit)
    d = inventory(packet)
    row = next(s for s in d['samples'] if s['sample']['sample_name']=='YSy150')
    assert row['alias_status'] == 'TEXT_MISMATCH'
    assert row['sample']['isolate'] == 'F2-93 '
    assert row['source_strain_row']['alias'] == 'F2-93'


def test_existing_output_never_overwritten(packet):
    p = packet / 'output.json'
    p.write_text('existing result\n')
    with pytest.raises(FileExistsError):
        main(['--input-dir', str(packet), '--output', str(p)])
    assert p.read_text() == 'existing result\n'
