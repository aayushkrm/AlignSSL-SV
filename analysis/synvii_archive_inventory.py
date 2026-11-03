"""Offline CNP0002230 metadata reconciliation; never downloads sequence data."""
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

SAMPLE = 'metadata_CNP0002230_sample_Microbial_sample.tsv'
EXPERIMENT = 'metadata_CNP0002230_experiment.tsv'
LINKS = 'cnsa-data-download-links.txt'
TABLE = 'source-table-s3.xlsx'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    require(path.is_file() and not path.is_symlink(), f'not a regular source: {path}')
    before = path.stat()
    require(before.st_size <= 1024**2, f'oversized source: {path}')
    data = path.read_bytes()
    after = path.stat()
    require((before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns), 'source changed during read')
    return data


def tsv(data, needed):
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig')), delimiter='\t')
    require(reader.fieldnames and len(set(reader.fieldnames)) == len(reader.fieldnames),
            'missing or duplicate TSV header')
    require(set(needed) <= set(reader.fieldnames), 'missing required TSV fields')
    rows = list(reader)
    require(0 < len(rows) <= 1000, 'invalid TSV row count')
    require(all(None not in r and all(v is not None for v in r.values()) for r in rows),
            'malformed TSV row')
    return rows


def strain_table(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        require(len(z.infolist()) <= 100 and sum(x.file_size for x in z.infolist()) <= 5*1024**2,
                'oversized workbook contents')
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(x.itertext()) for x in
                       ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        sheet = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    result = []
    for row in sheet.findall('s:sheetData/s:row', NS):
        cells = {}
        for c in row.findall('s:c', NS):
            require(c.find('s:f', NS) is None, 'formula in source strain table')
            ref = c.get('r', '')
            require(re.fullmatch(r'[A-Z]+[1-9][0-9]*', ref), 'invalid cell reference')
            col = re.match(r'[A-Z]+', ref).group()
            require(col not in cells, 'duplicate source cell')
            v = c.find('s:v', NS)
            text = '' if v is None else (v.text or '')
            if c.get('t') == 's':
                text = strings[int(text)]
            elif c.get('t') == 'inlineStr':
                text = ''.join(c.find('s:is', NS).itertext())
            cells[col] = text
        if cells.get('A', '').startswith(('YSy', 'BY')):
            result.append({'source_row': int(row.get('r')), 'strain_id': cells['A'],
                           'alias': cells.get('B', ''), 'genotype_marker_text': cells.get('C', ''),
                           'comment': cells.get('D', ''), 'notes': cells.get('E', '')})
    require(result, 'empty named-strain inventory')
    require(len({x['strain_id'] for x in result}) == len(result), 'duplicate strain ID')
    return result


def inventory(root):
    root = Path(root)
    data = {n: read(root/n) for n in (SAMPLE, EXPERIMENT, LINKS, TABLE)}
    samples = tsv(data[SAMPLE], ['sample_accession', 'sample_name', 'isolate', 'sample_title'])
    runs = tsv(data[EXPERIMENT], ['project_accession', 'sample_accession', 'sample_name',
                                  'experiment_accession', 'run_accession', 'library_strategy',
                                  'file_name', 'file_md5', 'file2_name', 'file2_md5',
                                  'file3_name', 'file3_md5'])
    by_sample = {x['sample_accession']: x for x in samples}
    require(len(by_sample) == len(samples), 'duplicate sample accession')
    require(len({x['sample_name'] for x in samples}) == len(samples), 'duplicate sample name')
    require(all(x['sample_accession'] and x['sample_name'] for x in samples), 'empty sample key')
    require(len({x['run_accession'] for x in runs}) == len(runs), 'duplicate run accession')
    expected, experiment_sample, per_sample = set(), {}, collections.defaultdict(list)
    for r in runs:
        require(r['project_accession'] == 'CNP0002230', 'foreign project')
        s = by_sample.get(r['sample_accession'])
        require(s is not None and s['sample_name'] == r['sample_name'], 'sample identity mismatch')
        for k, prefix in [('sample_accession','CNS'), ('experiment_accession','CNX'), ('run_accession','CNR')]:
            require(re.fullmatch(prefix+r'[0-9]+', r[k]), f'invalid {k}')
        exp = r['experiment_accession']
        require(experiment_sample.setdefault(exp, r['sample_accession']) == r['sample_accession'],
                'experiment has multiple samples')
        per_sample[r['sample_accession']].append(r)
        for f, m in [('file_name','file_md5'), ('file2_name','file2_md5'), ('file3_name','file3_md5')]:
            name, md5 = r[f], r[m]
            require(bool(name) == bool(md5), 'unpaired filename/checksum')
            if name:
                require(name not in ('.','..') and '/' not in name and '\\' not in name,
                        'invalid filename')
                require(re.fullmatch('[0-9a-fA-F]{32}', md5), 'invalid declared MD5')
                url = 'ftp://ftp.cngb.org/pub/CNSA/data5/CNP0002230/' + '/'.join(
                    [r['sample_accession'], exp, r['run_accession'], name])
                require(url not in expected, 'duplicate expected file')
                expected.add(url)
        require(r['file_name'], 'run without primary file')
    observed, sequence_links = set(), []
    for line in data[LINKS].decode().splitlines():
        parts = line.split()
        require(len(parts) == 2, 'malformed manifest line')
        kind, url = parts
        if kind == 'experiment':
            require(url not in observed, 'duplicate manifest file')
            observed.add(url)
        else:
            require(kind == 'sequence' and re.fullmatch(
                r'https://db.cngb.org/cnsa/ajax/download_sequence_txt/\?accession_id=N_[0-9]+', url),
                'unrecognized manifest entry')
            require(url not in sequence_links, 'duplicate sequence link')
            sequence_links.append(url)
    require(observed == expected, 'manifest/metadata file mismatch')
    require(set(per_sample) == set(by_sample), 'sample without run metadata')
    strains = strain_table(data[TABLE])
    by_name = {x['strain_id']: x for x in strains}
    joined = []
    for s in samples:
        source = by_name.get(s['sample_name'])
        alias = 'NO_SOURCE_STRAIN_ROW' if source is None else (
            'UNSPECIFIED_SOURCE_ALIAS' if source['alias'] in ('', '/') else
            'EXACT' if source['alias'] == s['isolate'] else 'TEXT_MISMATCH')
        joined.append({'sample': s, 'source_strain_row': source, 'alias_status': alias,
                       'runs': per_sample[s['sample_accession']]})
    return {'schema': 'synvii-archive-inventory-v1', 'status': 'METADATA_RECONCILED',
            'sources': {n: {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}
                        for n,b in data.items()},
            'counts': {'samples': len(samples), 'experiments': len(experiment_sample),
                       'runs': len(runs), 'raw_file_links': len(expected),
                       'reference_sequence_links': len(sequence_links), 'source_strains': len(strains)},
            'strategies': dict(collections.Counter(r['library_strategy'] for r in runs)),
            'alias_status_counts': dict(collections.Counter(x['alias_status'] for x in joined)),
            'source_strains_without_archive_sample': [x for x in strains
                if x['strain_id'] not in {s['sample_name'] for s in samples}],
            'sequence_links': sequence_links, 'samples': joined,
            'limits': ['Metadata reconciliation is not assay completeness or biological validation.',
                       'Declared raw-file MD5s were not verified against raw reads.',
                       'Marker genotype text is not an ordered SV path, dosage vector or ploidy label.',
                       'No quantitative phenotype or matched-dosage contrast is established.']}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args(argv)
    result = inventory(a.input_dir)
    with Path(a.output).open('x') as out:
        json.dump(result, out, indent=2, ensure_ascii=False)
        out.write('\n')


if __name__ == '__main__':
    main()
