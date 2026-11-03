"""Validate synthetic VCF inputs with EBI's native validator in a Slurm step."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def validate(path, validator, root):
    data = path.read_bytes()
    with tempfile.TemporaryDirectory(prefix='alignssl-vcf-validator-') as tmp:
        cmd = [str(validator), '-i', str(path), '-l', 'warning', '-r', 'summary', '-o', tmp]
        completed = subprocess.run(cmd, text=True, capture_output=True, check=False)
        reports = {p.name: p.read_text(errors='replace') for p in Path(tmp).iterdir() if p.is_file()}
    return {'input': str(path.relative_to(root)), 'input_sha256': hashlib.sha256(data).hexdigest(),
            'command': cmd[:-1] + ['<private temporary directory>'], 'exit_code': completed.returncode,
            'stdout': completed.stdout, 'stderr': completed.stderr, 'reports': reports}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-root', type=Path, required=True)
    p.add_argument('--validator', type=Path, required=True)
    a = p.parse_args()
    if not os.environ.get('SLURM_JOB_ID'):
        raise ValueError('run in the designated Slurm allocation')
    files = sorted(a.input_root.glob('run*/*.vcf'))
    if len(files) != 20 or len({p.parent.name for p in files}) != 4:
        raise ValueError('expected five VCFs for each of four preserved runs')
    workers = min(int(os.environ.get('SLURM_CPUS_PER_TASK', '1')), len(files))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda f: validate(f, a.validator, a.input_root), files))
    binary = a.validator.read_bytes()
    output = {'slurm_job_id': os.environ['SLURM_JOB_ID'],
              'node': os.environ.get('SLURMD_NODENAME'), 'allocated_cpus': workers,
              'validator_sha256': hashlib.sha256(binary).hexdigest(), 'results': results}
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
