"""Independently trace reciprocal BNDs through a six-end synthetic reference."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def fasta(path):
    lines = path.read_text().splitlines()
    if not lines or not lines[0].startswith('>') or any(x.startswith('>') for x in lines[1:]):
        raise ValueError(f'invalid single-record FASTA: {path}')
    return ''.join(lines[1:])


def records(path, reference):
    entries = {}
    for line in path.read_text().splitlines():
        if line.startswith('#'):
            continue
        fields = line.split('\t')
        if len(fields) != 10:
            raise ValueError('expected exactly one VCF sample')
        chrom, position, ident, ref, alt, _, filt, info, fmt, sample = fields
        position = int(position)
        meta = dict(x.split('=', 1) for x in info.split(';'))
        if chrom != 'chr1' or ref != reference[position-1] or filt != 'PASS':
            raise ValueError('invalid reference, chromosome, or filter')
        if meta.get('SVTYPE') != 'BND' or meta.get('EVENT') != 'event1' or fmt != 'GT' or sample != '0|1':
            raise ValueError('unexpected grouping, type, or genotype')
        right = re.fullmatch(r'A([\[\]])chr1:(\d+)\1', alt)
        left = re.fullmatch(r'([\[\]])chr1:(\d+)\1A', alt)
        match = right or left
        if not match or ident in entries:
            raise ValueError('invalid or repeated BND')
        entries[ident] = {'pos': position, 'side': 'R' if right else 'L',
                          'remote_side': 'R' if match.group(1) == ']' else 'L',
                          'remote_pos': int(match.group(2)), 'mate': meta['MATEID']}
    if set(entries) != set('abcdef'):
        raise ValueError('expected six labeled ends')
    for name, e in entries.items():
        other = entries[e['mate']]
        if other['mate'] != name or other['pos'] != e['remote_pos'] or other['side'] != e['remote_side']:
            raise ValueError('BND ALT and reciprocal MATEID disagree')
    return entries


def reconstruct(entries, reference):
    expected = {'a': (1000, 'R'), 'b': (1001, 'L'), 'c': (15000, 'R'),
                'd': (15001, 'L'), 'e': (30000, 'R'), 'f': (30001, 'L')}
    if any((entries[k]['pos'], entries[k]['side']) != v for k, v in expected.items()):
        raise ValueError('unexpected reference cut sides')
    block_b = reference[1000:15000]
    block_c = reference[15000:30000]
    def reverse_complement(s):
        return s.translate(str.maketrans('ACGT', 'TGCA'))[::-1]
    segments = {'b': ('c', block_b, 'B'), 'c': ('b', reverse_complement(block_b), 'reverse(B)'),
                'd': ('e', block_c, 'C'), 'e': ('d', reverse_complement(block_c), 'reverse(C)')}
    pieces, visited, current = [reference[:1000]], {'a'}, 'a'
    traversed = []
    while True:
        arrival = entries[current]['mate']
        if arrival == 'f':
            visited.add('f')
            break
        if arrival in visited or arrival not in segments:
            raise ValueError('cycle or disconnected derivative')
        departure, seq, label = segments[arrival]
        if departure in visited:
            raise ValueError('reused reference segment')
        visited.update((arrival, departure))
        pieces.append(seq)
        traversed.append(label)
        current = departure
    if visited != set(entries):
        raise ValueError('derivative does not traverse all ends')
    pieces.append(reference[30000:])
    edges = sorted({tuple(sorted((name, e['mate']))) for name, e in entries.items()})
    return ''.join(pieces), traversed, edges


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('fixtures', type=Path)
    a = p.parse_args()
    reference = fasta(a.fixtures / 'reference.fa')
    if len(reference) != 40000 or set(reference) - set('ACGT'):
        raise ValueError('unexpected synthetic reference')
    result = {}
    observed = {}
    for label, file in [('truth', 'truth.vcf'), ('rewired', 'rewired.vcf')]:
        recs = records(a.fixtures / file, reference)
        seq, traversal, edges = reconstruct(recs, reference)
        saved = fasta(a.fixtures / f'{label}_derivative.fa')
        if seq != saved:
            raise ValueError(f'{label} saved FASTA disagrees with BND traversal')
        observed[label] = (recs, seq, edges)
        result[label] = {'adjacencies': edges, 'reference_segment_path': traversal,
                         'length': len(seq), 'sequence_sha256': hashlib.sha256(seq.encode()).hexdigest(),
                         'saved_fasta_matches_traversal': True}
    first, second = observed['truth'], observed['rewired']
    if any((first[0][k]['pos'], first[0][k]['side']) != (second[0][k]['pos'], second[0][k]['side'])
           for k in first[0]) or first[2] == second[2] or first[1] == second[1]:
        raise ValueError('fixtures do not express the intended comparison')
    result['same_breakends_and_sides'] = True
    result['same_adjacencies'] = False
    result['same_derivative_sequence'] = False
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
