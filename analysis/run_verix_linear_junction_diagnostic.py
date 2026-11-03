"""Compare two explicit synthetic linear derivatives with the native Verix CLI."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from analysis.run_verix_junction_diagnostic import PIN, digest, vcf


def all_matchings(names):
    if not names:
        yield []
        return
    first = names[0]
    for i in range(1, len(names)):
        for rest in all_matchings(names[1:i] + names[i+1:]):
            yield [(first, names[i])] + rest


def connected_linear(pairs):
    reference_partners = {frozenset(x) for x in ('ab', 'cd', 'ef')}
    if any(frozenset(p) in reference_partners for p in pairs):
        return False
    graph = {x: [] for x in 'abcdef'}
    for a, b in pairs + [('b', 'c'), ('d', 'e')]:
        graph[a].append(b)
        graph[b].append(a)
    seen, pending = set(), ['a']
    while pending:
        node = pending.pop()
        if node not in seen:
            seen.add(node)
            pending.extend(graph[node])
    return len(seen) == 6 and len(graph['a']) == len(graph['f']) == 1


def write_fasta(path, name, sequence):
    path.write_text('>' + name + '\n' + '\n'.join(sequence[i:i+80]
                    for i in range(0, len(sequence), 80)) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--verix', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    head = subprocess.check_output(['git', '-C', str(a.source), 'rev-parse', 'HEAD'], text=True).strip()
    if head != PIN:
        raise ValueError(f'unexpected source revision {head}')
    pairs = [m for m in all_matchings('abcdef') if connected_linear(m)]
    expected = [[('a', 'c'), ('b', 'e'), ('d', 'f')],
                [('a', 'd'), ('b', 'e'), ('c', 'f')]]
    if pairs[:2] != expected:
        raise ValueError('unexpected graph enumeration')
    pos = {'a': 1000, 'b': 1001, 'c': 15000, 'd': 15001, 'e': 30000, 'f': 30001}
    orient = {'a': 'R', 'b': 'L', 'c': 'R', 'd': 'L', 'e': 'R', 'f': 'L'}
    bases = ['ACGT'[hashlib.sha256(f'alignssl-fixture-{i}'.encode()).digest()[0] % 4]
             for i in range(40000)]
    for coordinate in (*pos.values(), 32000):
        bases[coordinate - 1] = 'A'
    ref = ''.join(bases)
    prefix, segment_b, segment_c, suffix = ref[:1000], ref[1000:15000], ref[15000:30000], ref[30000:]
    def rc(s):
        return s.translate(str.maketrans('ACGT', 'TGCA'))[::-1]
    truth_path = prefix + rc(segment_b) + rc(segment_c) + suffix
    query_path = prefix + segment_c + segment_b + suffix
    if len(truth_path) != len(ref) or len(query_path) != len(ref) or truth_path == query_path:
        raise ValueError('synthetic path construction failed')
    a.output.mkdir(parents=True, exist_ok=False)
    fixtures = a.output / 'fixtures'
    fixtures.mkdir()
    write_fasta(fixtures / 'reference.fa', 'chr1', ref)
    write_fasta(fixtures / 'truth_derivative.fa', 'truth_derivative', truth_path)
    write_fasta(fixtures / 'rewired_derivative.fa', 'rewired_derivative', query_path)
    vcf(fixtures / 'truth.vcf', pairs[0], pos, orient)
    vcf(fixtures / 'rewired.vcf', pairs[1], pos, orient)
    vcf(fixtures / 'position_control.vcf', pairs[0], {**pos, 'c': 32000}, orient)
    vcf(fixtures / 'orientation_control.vcf', pairs[0], pos, {**orient, 'c': 'L'})
    vcf(fixtures / 'genotype_control.vcf', pairs[0], pos, orient, genotype='1|1')
    summary = {'eligible_pairings_in_lexical_order': pairs, 'selected_truth': pairs[0],
               'selected_rewired': pairs[1], 'reference_length': len(ref),
               'derivative_lengths': [len(truth_path), len(query_path)],
               'derivative_sequences_identical': truth_path == query_path}
    (fixtures / 'construction.json').write_text(json.dumps(summary, indent=2) + '\n')
    strict = ['--breakend_mode', '--enforce_type', '--enforce_genotype', '--enforce_ins',
              '--match_thr', '0', '--merge_thr', '0']
    cases = [('default_self', 'truth.vcf', []), ('default_rewired', 'rewired.vcf', []),
             ('strict_self', 'truth.vcf', strict), ('strict_rewired', 'rewired.vcf', strict),
             ('strict_position_control', 'position_control.vcf', strict),
             ('strict_orientation_control', 'orientation_control.vcf', strict),
             ('strict_genotype_control', 'genotype_control.vcf', strict)]
    records = []
    for name, query, flags in cases:
        cmd = [str(a.verix), 'bench', '--query', str(fixtures / query), '--target',
               str(fixtures / 'truth.vcf'), '--output_dir', str(a.output / name),
               '--formats', 'multi', 'multi', '--csv_links', 'EVENT', 'EVENT'] + flags
        completed = subprocess.run(cmd, text=True, capture_output=True, check=False)
        (a.output / f'{name}.stdout.txt').write_text(completed.stdout)
        (a.output / f'{name}.stderr.txt').write_text(completed.stderr)
        records.append({'name': name, 'query': query, 'flags': flags,
                        'exit_code': completed.returncode, 'command': cmd})
    files = sorted(x for x in a.output.rglob('*') if x.is_file())
    receipt = {'native_git_commit': head, 'cases': records,
               'sha256': {str(x.relative_to(a.output)): digest(x) for x in files}}
    (a.output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    if any(x['exit_code'] for x in records):
        raise SystemExit('at least one native command failed; outputs preserved')


if __name__ == '__main__':
    main()
