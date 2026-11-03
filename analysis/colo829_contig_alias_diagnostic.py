"""Test native Verix BND grouping before and after a case-only ALT alias change."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from analysis.run_verix_junction_diagnostic import PIN

EXPECTED = 'ae2d7b02fea3dda159e602c6124ef1911324efb692682ad9977eac697d6e5042'
CONTIG = re.compile(rb'^##contig=<ID=([^,>]+)')
REMOTE = re.compile(rb'([\[\]])([^:\[\]]+):(\d+)\1')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def normalized_copy(data):
    lines = data.splitlines(keepends=True)
    names = [m.group(1) for line in lines if (m := CONTIG.match(line))]
    if not names or len(set(names)) != len(names):
        raise ValueError('missing or duplicate contig IDs')
    aliases = {}
    for name in names:
        aliases.setdefault(name.lower(), []).append(name)
    counts = {'header_contigs': len(names), 'all_records': 0, 'bnd_records': 0,
              'already_exact': 0, 'case_only_changes': 0}
    changes, output = [], []
    for line in lines:
        if line.startswith(b'#'):
            output.append(line)
            continue
        newline = b'\n' if line.endswith(b'\n') else b''
        content = line[:-1] if newline else line
        fields = content.split(b'\t')
        if len(fields) < 8:
            raise ValueError('malformed VCF row')
        counts['all_records'] += 1
        if b'SVTYPE=BND' in fields[7].split(b';'):
            counts['bnd_records'] += 1
            found = list(REMOTE.finditer(fields[4]))
            if len(found) != 1 or b',' in fields[4]:
                raise ValueError('BND ALT has unsupported or multiple mate tokens')
            m = found[0]
            remote = m.group(2)
            candidates = aliases.get(remote.lower(), [])
            if len(candidates) != 1:
                raise ValueError(f'mate contig has no unique case-only alias: {remote!r}')
            canonical = candidates[0]
            if remote == canonical:
                counts['already_exact'] += 1
            else:
                original_alt = fields[4]
                fields[4] = original_alt[:m.start(2)] + canonical + original_alt[m.end(2):]
                counts['case_only_changes'] += 1
                changes.append({'record_id': fields[2].decode(), 'local_chrom': fields[0].decode(),
                                'local_pos': int(fields[1]), 'remote_original': remote.decode(),
                                'remote_header_alias': canonical.decode()})
        output.append(b'\t'.join(fields) + newline)
    return b''.join(output), counts, changes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--normalized', type=Path, required=True, help='New output gzip outside Git')
    p.add_argument('--output', type=Path, required=True, help='New native results directory')
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--verix', type=Path, required=True)
    a = p.parse_args()
    original = a.input.read_bytes()
    if sha(original) != EXPECTED:
        raise ValueError('unexpected source SHA256')
    commit = subprocess.check_output(['git', '-C', str(a.source), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != PIN:
        raise ValueError('unexpected native source commit')
    if a.output.exists() or a.normalized.exists():
        raise ValueError('output already exists')
    decoded = gzip.decompress(original)
    corrected, counts, changes = normalized_copy(decoded)
    if sha(a.input.read_bytes()) != EXPECTED:
        raise ValueError('source changed during normalization')
    a.output.mkdir(parents=True, exist_ok=False)
    with a.normalized.open('xb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as gz:
            gz.write(corrected)
    if gzip.decompress(a.normalized.read_bytes()) != corrected:
        raise ValueError('normalized gzip failed round-trip')
    manifest = {'source_sha256': sha(original), 'source_uncompressed_sha256': sha(decoded),
                'normalized_sha256': sha(a.normalized.read_bytes()),
                'normalized_uncompressed_sha256': sha(corrected), 'counts': counts, 'changes': changes,
                'scope': 'BND ALT remote chromosome name only; INFO/ANN remain untouched',
                'native_git_commit': commit}
    (a.output / 'normalization.json').write_text(json.dumps(manifest, indent=2) + '\n')
    flags = ['--breakend_mode', '--match_thr', '0', '--merge_thr', '0']
    cases = [('original_self', a.input, a.input), ('normalized_self', a.normalized, a.normalized),
             ('original_to_normalized', a.input, a.normalized),
             ('normalized_to_original', a.normalized, a.input)]
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
        completed = list(pool.map(execute, cases))
    files = sorted(x for x in a.output.rglob('*') if x.is_file())
    receipt = {'native_git_commit': commit, 'cases': completed,
               'sha256': {str(x.relative_to(a.output)): sha(x.read_bytes()) for x in files}}
    (a.output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    if any(x['exit_code'] for x in completed):
        raise SystemExit('one or more native commands failed; outputs preserved')


if __name__ == '__main__':
    main()
