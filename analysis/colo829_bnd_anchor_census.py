"""Exploratory all-record BND anchor census; do not infer errors from mismatches."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re

EXPECTED = {
    'caller.vcf.gz': 'ae2d7b02fea3dda159e602c6124ef1911324efb692682ad9977eac697d6e5042',
    'truth.vcf': 'a8f38454367cf8837a7dba1d29c9bc338a8e62cadfee6d2489931f8105f0dcdc',
}
RIGHT = re.compile(r'^([ACGTN]+)([\[\]])([^:\[\]]+):(\d+)\2$', re.IGNORECASE)
LEFT = re.compile(r'^([\[\]])([^:\[\]]+):(\d+)\1([ACGTN]+)$', re.IGNORECASE)


def chromosome(value):
    return re.sub(r'^chr', '', value, flags=re.IGNORECASE).upper()


def parse_bnd(fields):
    """Classify one BND record; unsupported representations stay explicit."""
    chrom, pos, ident, ref, alt, qual, filt, info = fields[:8]
    metadata = dict(x.split('=', 1) if '=' in x else (x, '') for x in info.split(';'))
    base = {'chrom': chrom, 'pos': int(pos), 'id': ident, 'ref': ref, 'alt': alt,
            'qual': qual, 'filter': filt, 'mate_ids': metadata.get('MATEID', '').split(',')
            if metadata.get('MATEID') else [], 'event': metadata.get('EVENT'),
            'declared_insertion_sequence': metadata.get('SVINSSEQ'),
            'declared_insertion_length': metadata.get('SVINSLEN')}
    if len(ref) != 1 or ref.upper() not in 'ACGT':
        return {**base, 'parse_status': 'UNKNOWN_NON_SINGLE_ACGT_REF'}
    right, left = RIGHT.fullmatch(alt), LEFT.fullmatch(alt)
    if right:
        local, bracket, remote_chrom, remote_pos = right.groups()
        side, anchor, extra = 'R', local[0], local[1:]
    elif left:
        bracket, remote_chrom, remote_pos, local = left.groups()
        side, anchor, extra = 'L', local[-1], local[:-1]
    else:
        return {**base, 'parse_status': 'UNKNOWN_ALT_REPRESENTATION'}
    if anchor.upper() not in 'ACGT':
        return {**base, 'parse_status': 'UNKNOWN_NON_ACGT_ANCHOR'}
    return {**base, 'parse_status': 'PARSED', 'side': side,
            'remote_side': 'R' if bracket == ']' else 'L', 'remote_chrom': remote_chrom,
            'remote_pos': int(remote_pos), 'local_anchor': anchor.upper(),
            'other_local_literal': extra.upper(), 'anchor_matches_local_ref': anchor.upper() == ref.upper()}


def pair_records(records):
    coords = defaultdict(list)
    for i, e in enumerate(records):
        if e['parse_status'] == 'PARSED':
            coords[(chromosome(e['chrom']), e['pos'])].append(i)
    candidates = {}
    for i, e in enumerate(records):
        if e['parse_status'] != 'PARSED':
            continue
        matches = []
        for j in coords[(chromosome(e['remote_chrom']), e['remote_pos'])]:
            if i == j:
                continue
            other = records[j]
            compatible = (chromosome(other['remote_chrom']) == chromosome(e['chrom']) and
                          other['remote_pos'] == e['pos'] and other['side'] == e['remote_side'] and
                          other['remote_side'] == e['side'])
            compatible &= not e['mate_ids'] or other['id'] in e['mate_ids']
            compatible &= not other['mate_ids'] or e['id'] in other['mate_ids']
            if compatible:
                matches.append(j)
        candidates[i] = matches
    for i, e in enumerate(records):
        if e['parse_status'] != 'PARSED':
            e['mate_status'] = 'UNKNOWN_UNPARSED'
            continue
        matches = candidates[i]
        if not matches:
            e['mate_status'] = 'UNKNOWN_NO_RECIPROCAL_RECORD'
        elif len(matches) != 1:
            e['mate_status'] = 'UNKNOWN_MULTIPLE_RECIPROCAL_RECORDS'
        elif candidates.get(matches[0]) != [i]:
            e['mate_status'] = 'UNKNOWN_ASYMMETRIC_PAIRING'
        else:
            other = records[matches[0]]
            e['mate_status'] = 'UNIQUE_RECIPROCAL'
            e['reciprocal_id'] = other['id']
            e['reciprocal_ref'] = other['ref'].upper()
            e['anchor_matches_reciprocal_ref'] = e['local_anchor'] == other['ref'].upper()
    return records


def census(path):
    opener = gzip.open if path.suffix == '.gz' else open
    types, records, samples, reference = Counter(), [], [], []
    with opener(path, 'rt', encoding='utf-8') as f:
        for line in f:
            if line.startswith('##reference='):
                reference.append(line.rstrip('\n').split('=', 1)[1])
            if line.startswith('#CHROM\t'):
                samples = line.rstrip('\n').split('\t')[9:]
            if line.startswith('#'):
                continue
            fields = line.rstrip('\n').split('\t')
            if len(fields) < 8:
                raise ValueError('malformed VCF row')
            values = dict(x.split('=', 1) if '=' in x else (x, '') for x in fields[7].split(';'))
            svtype = values.get('SVTYPE', 'UNSPECIFIED')
            types[svtype] += 1
            if svtype == 'BND':
                records.append(parse_bnd(fields))
    pair_records(records)
    counts = Counter()
    for e in records:
        counts['bnd_records'] += 1
        counts[e['parse_status']] += 1
        counts[e['mate_status']] += 1
        if e['parse_status'] != 'PARSED':
            continue
        if e['anchor_matches_local_ref']:
            counts['local_anchor_matches_ref'] += 1
        else:
            counts['local_anchor_differs_ref'] += 1
            counts['local_anchor_differs_ref_side_' + e['side']] += 1
            if e['mate_status'] == 'UNIQUE_RECIPROCAL':
                key = ('different_local_anchor_equals_mate_ref' if e['anchor_matches_reciprocal_ref']
                       else 'different_local_anchor_differs_mate_ref')
                counts[key] += 1
            else:
                counts['different_local_anchor_mate_unknown'] += 1
    return {'sample_names': samples, 'reference_headers': reference, 'all_record_svtypes': dict(types),
            'counts': dict(counts), 'bnd_records': records}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    sources, results = {}, {}
    for name, expected in EXPECTED.items():
        path = a.input_dir / name
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != expected:
            raise ValueError(f'source checksum differs: {name}')
        sources[name] = {'bytes': len(data), 'sha256': digest}
        results[name] = census(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f'source changed during read: {name}')
    result = {'schema': 'colo829-bnd-anchor-census-v1', 'sources': sources, 'results': results,
              'scope': ['Exploratory whole-file counts, not an unbiased sample of callers.',
                        'An ALT local anchor differing from REF can encode a real replacement.',
                        'A reciprocal match does not validate an allele, clone, or haplotype.',
                        'Unsupported or ambiguous records are UNKNOWN, never forced into a match.']}
    with a.output.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')


if __name__ == '__main__':
    main()
