"""Repeat the COLO829 alias diagnostic with two seekable plain VCF inputs."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess

from analysis.colo829_contig_alias_diagnostic import EXPECTED, normalized_copy
from analysis.run_verix_junction_diagnostic import PIN


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original', type=Path, required=True)
    p.add_argument('--normalized-gzip', type=Path, required=True)
    p.add_argument('--prior-result', type=Path, required=True)
    p.add_argument('--original-plain', type=Path, required=True)
    p.add_argument('--normalized-plain', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--verix', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists() or a.original_plain.exists() or a.normalized_plain.exists():
        raise ValueError('a new output directory and new input paths are required')
    original_bytes = a.original.read_bytes()
    normalized_bytes = a.normalized_gzip.read_bytes()
    old_manifest = json.loads((a.prior_result / 'normalization.json').read_text())
    old_receipt = (a.prior_result / 'receipt.json').read_bytes()
    if sha(original_bytes) != EXPECTED or sha(normalized_bytes) != old_manifest['normalized_sha256']:
        raise ValueError('input differs from recorded source or normalized copy')
    original = gzip.decompress(original_bytes)
    normalized = gzip.decompress(normalized_bytes)
    expected, counts, changes = normalized_copy(original)
    if (normalized != expected or counts != old_manifest['counts'] or
            changes != old_manifest['changes'] or sha(original) != old_manifest['source_uncompressed_sha256'] or
            sha(normalized) != old_manifest['normalized_uncompressed_sha256']):
        raise ValueError('uncompressed inputs differ from original normalization manifest')
    commit = subprocess.check_output(['git', '-C', str(a.source), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != PIN:
        raise ValueError('unexpected native source commit')
    a.output.mkdir(parents=True, exist_ok=False)
    for path, contents in [(a.original_plain, original), (a.normalized_plain, normalized)]:
        with path.open('xb') as f:
            f.write(contents)
    manifest = {'prior_receipt_sha256': sha(old_receipt), 'original_gzip_sha256': sha(original_bytes),
                'normalized_gzip_sha256': sha(normalized_bytes), 'original_plain_sha256': sha(original),
                'normalized_plain_sha256': sha(normalized), 'counts': counts, 'changes': changes,
                'change_from_prior_attempt': 'both VCFs are uncompressed and seekable; content unchanged',
                'scope': 'BND ALT remote contig case only; INFO/ANN remain untouched',
                'native_git_commit': commit}
    (a.output / 'input-check.json').write_text(json.dumps(manifest, indent=2) + '\n')
    flags = ['--breakend_mode', '--match_thr', '0', '--merge_thr', '0']
    cases = [('original_self', a.original_plain, a.original_plain),
             ('normalized_self', a.normalized_plain, a.normalized_plain),
             ('original_to_normalized', a.original_plain, a.normalized_plain),
             ('normalized_to_original', a.normalized_plain, a.original_plain)]
    def execute(case):
        name, query, target = case
        cmd = [str(a.verix), 'bench', '--query', str(query), '--target', str(target),
               '--output_dir', str(a.output / name)] + flags
        env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
        done = subprocess.run(cmd, text=True, capture_output=True, check=False, env=env)
        (a.output / f'{name}.stdout.txt').write_text(done.stdout)
        (a.output / f'{name}.stderr.txt').write_text(done.stderr)
        return {'name': name, 'command': cmd, 'exit_code': done.returncode}
    with ThreadPoolExecutor(max_workers=len(cases)) as pool:
        results = list(pool.map(execute, cases))
    files = sorted(x for x in a.output.rglob('*') if x.is_file())
    receipt = {'native_git_commit': commit, 'cases': results,
               'sha256': {str(x.relative_to(a.output)): sha(x.read_bytes()) for x in files}}
    (a.output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    if any(x['exit_code'] for x in results):
        raise SystemExit('one or more native commands failed; outputs preserved')


if __name__ == '__main__':
    main()
