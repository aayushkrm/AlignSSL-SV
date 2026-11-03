"""Inspect which source BND records native Verix groups in each input."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from verix.io import VCFFormat, parse_vcf


def inspect(path):
    callset = parse_vcf(str(path), VCFFormat.DEFAULT, None, 'SVTYPE', 0, None, 0,
                        breakend_mode=True)
    groups = []
    for sv in callset.svs:
        records = []
        for rec in sv.records:
            mate = rec.info.get('MATEID')
            mates = list(mate) if isinstance(mate, (list, tuple)) else ([mate] if mate else [])
            records.append({'id': rec.id, 'mate_ids': mates, 'chrom': rec.chrom, 'pos': rec.pos})
        is_pair = (len(records) == 2 and records[0]['mate_ids'] == [records[1]['id']] and
                   records[1]['mate_ids'] == [records[0]['id']])
        groups.append({'native_group_id': str(sv.id), 'records': records,
                       'two_records_with_reciprocal_mate_ids': is_pair})
    return {'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'group_count': len(groups), 'group_sizes': dict(Counter(str(len(x['records'])) for x in groups)),
            'groups_with_reciprocal_mate_ids': sum(x['two_records_with_reciprocal_mate_ids'] for x in groups),
            'groups': groups}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original', type=Path, required=True)
    p.add_argument('--normalized', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps({'original': inspect(a.original), 'normalized': inspect(a.normalized)}, indent=2))


if __name__ == '__main__':
    main()
