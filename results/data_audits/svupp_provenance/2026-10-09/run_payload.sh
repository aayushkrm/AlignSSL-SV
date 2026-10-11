#!/usr/bin/env bash
set -euo pipefail
cd /beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/svupp-provenance-20261009-01
provenance_python=/home/igorno/miniconda3/envs/truvari_env/bin/python
"$provenance_python" -c 'import sys, pytest, json; versions={"python":sys.version.split()[0],"pytest":pytest.__version__}; print(json.dumps(versions)); assert versions == {"python":"3.10.20","pytest":"8.4.2"}'
"$provenance_python" - <<'PY'
import os
from pathlib import Path
import stat
import sys
from analysis.inspect_pinned_research_zip import _open_parent_without_symlinks
from analysis.run_svupp_provenance_headers import SOURCE, SOURCE_BYTES, new_metadata, trusted_root

assert sys.platform.startswith("linux") and os.geteuid() != 0
assert all(hasattr(os, name) for name in ("O_PATH", "O_DIRECTORY", "O_NOFOLLOW"))
root = trusted_root(Path.cwd())
for target in (root / "unused-preflight-name", SOURCE):
    fd = _open_parent_without_symlinks(target)
    try:
        descriptor = os.fstat(fd)
        named = target.parent.stat()
        assert (descriptor.st_dev, descriptor.st_ino) == (named.st_dev, named.st_ino)
    finally:
        os.close(fd)
source = SOURCE.lstat()
assert stat.S_ISREG(source.st_mode) and source.st_nlink == 1 and source.st_size == SOURCE_BYTES
assert os.access(SOURCE, os.R_OK, effective_ids=True)
new_metadata(root / "permission_preflight.json", {
    "status": "LIVE_PROVENANCE_ROOT_SOURCE_METADATA_PASS", "euid": os.geteuid(),
    "egid": os.getegid(), "root": str(root), "source": str(SOURCE),
    "source_identity": [source.st_dev, source.st_ino], "source_bytes": source.st_size,
    "source_body_read": False, "genotype_records_not_interpreted": True})
PY
cd code
"$provenance_python" -m pytest -q -rA -p no:cacheprovider --basetemp ../control_tmp \
 tests/test_svupp_provenance_headers.py tests/test_svupp_provenance_launcher.py \
 > ../controls.stdout.log 2> ../controls.stderr.log
tail -n 1 ../controls.stdout.log | grep -Eq '^44 passed(, [0-9]+ warnings?)? in [0-9.]+s$'
"$provenance_python" - <<'PY'
import os
from pathlib import Path
import stat
total = count = 0
for directory, dirs, files in os.walk("../control_tmp", followlinks=False):
    for name in dirs + files:
        info = (Path(directory) / name).lstat()
        count += 1
        if stat.S_ISREG(info.st_mode):
            total += info.st_size
        else:
            assert stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode)
        assert total <= 8 * 1024**2 and count <= 4096
print("control_bytes", total, "control_entries", count)
PY
cd ..
sha256sum -c bundle.sha256
"$provenance_python" code/analysis/run_svupp_provenance_headers.py --root "$PWD"
sha256sum -c bundle.sha256
"$provenance_python" -c 'import json; from pathlib import Path; r=json.loads(Path("result.json").read_text()); assert r["status"]=="COMPLETE_PROVENANCE_HEADERS" and r["genotype_records_not_interpreted"] and not r["publication_result"]; assert not Path("failure.json").exists()'
