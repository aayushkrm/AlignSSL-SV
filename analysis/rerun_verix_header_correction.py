"""Preserve old packets and repeat identical Verix cases with a VCF header fix."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

OLD = b'##INFO=<ID=MATEID,Number=1,Type=String,Description="Reciprocal breakend ID">'
NEW = b'##INFO=<ID=MATEID,Number=.,Type=String,Description="Reciprocal breakend ID">'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prepare(source, output):
    receipt_bytes = (source / 'receipt.json').read_bytes()
    receipt = json.loads(receipt_bytes)
    for name, expected in receipt['sha256'].items():
        if sha((source / name).read_bytes()) != expected:
            raise ValueError(f'original receipt mismatch: {name}')
    output.mkdir(parents=True, exist_ok=False)
    fixtures = output / 'fixtures'
    fixtures.mkdir()
    changes = []
    for item in sorted((source / 'fixtures').iterdir()):
        if not item.is_file():
            raise ValueError(f'unexpected fixture: {item}')
        original = item.read_bytes()
        if item.suffix == '.vcf':
            if original.count(OLD) != 1 or NEW in original:
                raise ValueError(f'unexpected original header: {item}')
            revised = original.replace(OLD, NEW, 1)
            if revised.replace(NEW, OLD, 1) != original:
                raise ValueError('non-header content changed')
        else:
            revised = original
        (fixtures / item.name).write_bytes(revised)
        changes.append({'file': item.name, 'original_sha256': sha(original),
                        'corrected_sha256': sha(revised), 'header_corrected': item.suffix == '.vcf'})
    record = {'original_receipt_sha256': sha(receipt_bytes), 'original_directory': str(source),
              'change': 'MATEID header Number=1 to Number=.; all other input bytes unchanged',
              'fixtures': changes}
    (output / 'header-correction.json').write_text(json.dumps(record, indent=2) + '\n')
    return receipt


def run_case(verix, output, case):
    name, query, flags = case['name'], case['query'], case['flags']
    fixtures = output / 'fixtures'
    cmd = [str(verix), 'bench', '--query', str(fixtures / query), '--target',
           str(fixtures / 'truth.vcf'), '--output_dir', str(output / name),
           '--formats', 'multi', 'multi', '--csv_links', 'EVENT', 'EVENT'] + flags
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    result = subprocess.run(cmd, text=True, capture_output=True, check=False, env=env)
    (output / f'{name}.stdout.txt').write_text(result.stdout)
    (output / f'{name}.stderr.txt').write_text(result.stderr)
    return {'name': name, 'query': query, 'flags': flags, 'exit_code': result.returncode, 'command': cmd}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original01', type=Path, required=True)
    p.add_argument('--original02', type=Path, required=True)
    p.add_argument('--output03', type=Path, required=True)
    p.add_argument('--output04', type=Path, required=True)
    p.add_argument('--verix', type=Path, required=True)
    p.add_argument('--workers', type=int, default=8)
    a = p.parse_args()
    if a.workers < 1 or a.output03.exists() or a.output04.exists():
        raise ValueError('invalid worker count or existing output')
    inputs = [(a.original01, a.output03), (a.original02, a.output04)]
    prepared = [(output, prepare(source, output)) for source, output in inputs]
    work = [(output, case) for output, receipt in prepared for case in receipt['cases']]
    with ThreadPoolExecutor(max_workers=min(a.workers, len(work))) as pool:
        results = list(pool.map(lambda pair: (pair[0], run_case(a.verix, *pair)), work))
    errors = False
    for output, original in prepared:
        cases = [result for dest, result in results if dest == output]
        files = sorted(x for x in output.rglob('*') if x.is_file())
        data = {'native_git_commit': original['native_git_commit'], 'cases': cases,
                'workers': min(a.workers, len(work)),
                'child_thread_environment': {'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1',
                                             'MKL_NUM_THREADS': '1'},
                'sha256': {str(x.relative_to(output)): sha(x.read_bytes()) for x in files}}
        (output / 'receipt.json').write_text(json.dumps(data, indent=2) + '\n')
        errors |= any(case['exit_code'] for case in cases)
    if errors:
        raise SystemExit('at least one native command failed; outputs preserved')


if __name__ == '__main__':
    main()
