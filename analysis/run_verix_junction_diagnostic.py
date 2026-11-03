"""Run a synthetic, reciprocal-BND interface diagnostic against native Verix.

This does not score real reads, establish a caller error, or test novelty.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

PIN = '7cb8524a941ce0d81dd04b0de51e009199386614'
CHROM = 'chr1'
HEADER = '''##fileformat=VCFv4.3
##contig=<ID=chr1,length=40000>
##INFO=<ID=SVTYPE,Number=1,Type=String,Description="Structural variant type">
##INFO=<ID=MATEID,Number=1,Type=String,Description="Reciprocal breakend ID">
##INFO=<ID=EVENT,Number=1,Type=String,Description="Shared synthetic event">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE
'''


def vcf(path, pairs, positions, directions, genotype='0|1'):
    """Emit four reciprocal records, using VCF local/remote breakend directions."""
    mate = {a: b for pair in pairs for a, b in (pair, pair[::-1])}
    if set(mate) != set(positions) or any(mate[mate[k]] != k for k in mate):
        raise ValueError('pairs must form a reciprocal matching')
    lines = [HEADER]
    for name in sorted(positions, key=positions.get):
        other = mate[name]
        bracket = ']' if directions[other] == 'R' else '['
        remote = f'{bracket}{CHROM}:{positions[other]}{bracket}'
        alt = 'A' + remote if directions[name] == 'R' else remote + 'A'
        info = f'SVTYPE=BND;MATEID={other};EVENT=event1'
        lines.append(f'{CHROM}\t{positions[name]}\t{name}\tA\t{alt}\t.\tPASS\t{info}\tGT\t{genotype}\n')
    path.write_text(''.join(lines))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True, help='Pinned Verix Git checkout')
    p.add_argument('--verix', type=Path, required=True, help='Native Verix CLI')
    p.add_argument('--output', type=Path, required=True, help='New output directory')
    a = p.parse_args()
    head = subprocess.check_output(['git', '-C', str(a.source), 'rev-parse', 'HEAD'], text=True).strip()
    if head != PIN:
        raise ValueError(f'unexpected source revision {head}')
    a.output.mkdir(parents=True, exist_ok=False)
    fixtures = a.output / 'fixtures'
    fixtures.mkdir()
    (fixtures / 'reference.fa').write_text('>chr1\n' + ('A' * 80 + '\n') * 500)
    pos = {'a': 1000, 'b': 1001, 'c': 30000, 'd': 30001}
    orient = {'a': 'R', 'b': 'L', 'c': 'R', 'd': 'L'}
    truth = [('a', 'c'), ('b', 'd')]
    changed = [('a', 'd'), ('b', 'c')]
    vcf(fixtures / 'truth.vcf', truth, pos, orient)
    vcf(fixtures / 'rewired.vcf', changed, pos, orient)
    vcf(fixtures / 'position_control.vcf', truth, {**pos, 'c': 32000}, orient)
    vcf(fixtures / 'orientation_control.vcf', truth, pos, {**orient, 'c': 'L'})
    vcf(fixtures / 'genotype_control.vcf', truth, pos, orient, genotype='1|1')
    strict = ['--breakend_mode', '--enforce_type', '--enforce_genotype', '--enforce_ins',
              '--match_thr', '0', '--merge_thr', '0']
    cases = [
        ('default_self', 'truth.vcf', []),
        ('default_rewired', 'rewired.vcf', []),
        ('strict_self', 'truth.vcf', strict),
        ('strict_rewired', 'rewired.vcf', strict),
        ('strict_position_control', 'position_control.vcf', strict),
        ('strict_orientation_control', 'orientation_control.vcf', strict),
        ('strict_genotype_control', 'genotype_control.vcf', strict),
    ]
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
