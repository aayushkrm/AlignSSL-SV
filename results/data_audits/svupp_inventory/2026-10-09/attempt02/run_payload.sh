#!/usr/bin/env bash
set -euo pipefail
cd /beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/svupp-inventory-20261009-02
inventory_python=/home/igorno/miniconda3/envs/truvari_env/bin/python
"$inventory_python" -c 'import sys, pytest, json; versions={"python":sys.version.split()[0],"pytest":pytest.__version__}; print(json.dumps(versions)); assert versions == {"python":"3.10.20","pytest":"8.4.2"}'
"$inventory_python" - <<'PY'
import os
from pathlib import Path
import stat
import sys
from analysis.inspect_pinned_research_zip import _open_parent_without_symlinks
from analysis.run_svupp_archive_inventory import ROOT, new_metadata, trusted_root

assert sys.platform.startswith("linux")
assert os.geteuid() != 0
assert all(hasattr(os, name) for name in ("O_PATH", "O_DIRECTORY", "O_NOFOLLOW"))
root = trusted_root(Path.cwd())
assert root == ROOT
ancestors = []
for directory in list(reversed(root.parents)) + [root]:
    info = directory.stat()
    assert stat.S_ISDIR(info.st_mode)
    ancestors.append({"path": str(directory), "mode": oct(stat.S_IMODE(info.st_mode)),
                      "uid": info.st_uid, "gid": info.st_gid,
                      "read_access": os.access(directory, os.R_OK, effective_ids=True),
                      "search_access": os.access(directory, os.X_OK, effective_ids=True)})
    assert ancestors[-1]["search_access"]
fd = _open_parent_without_symlinks(root / "unused-preflight-name")
try:
    descriptor = os.fstat(fd)
    named = root.stat()
    assert (descriptor.st_dev, descriptor.st_ino) == (named.st_dev, named.st_ino)
    leaf_info = os.stat("reservation.json", dir_fd=fd, follow_symlinks=False)
    assert stat.S_ISREG(leaf_info.st_mode) and leaf_info.st_nlink == 1
    leaf = os.open("reservation.json", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
    try:
        opened = os.fstat(leaf)
        assert (opened.st_dev, opened.st_ino) == (leaf_info.st_dev, leaf_info.st_ino)
        assert stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1
    finally:
        os.close(leaf)
finally:
    os.close(fd)
new_metadata(root / "permission_preflight.json", {
    "status": "LIVE_OPATH_DIRECTORY_REFERENCE_PASS", "euid": os.geteuid(),
    "egid": os.getegid(), "groups": os.getgroups(), "ancestors": ancestors,
    "root_identity": [named.st_dev, named.st_ino],
    "member_bodies_decoded": False, "genomic_scoring": False})
PY
cd code
"$inventory_python" -m pytest -q -rA -p no:cacheprovider --basetemp ../control_tmp \
 tests/test_pinned_research_zip.py tests/test_svupp_archive_launcher.py \
 tests/test_pinned_research_zip_permissions.py \
 > ../controls.stdout.log 2> ../controls.stderr.log
tail -n 1 ../controls.stdout.log | grep -Eq '^33 passed(, [0-9]+ warnings?)? in [0-9.]+s$'
"$inventory_python" -c 'from analysis.run_svupp_archive_inventory import control_tree_size; print("control_bytes", control_tree_size("../control_tmp"))'
cd ..
sha256sum -c bundle.sha256
"$inventory_python" code/analysis/run_svupp_archive_inventory.py --root "$PWD"
sha256sum -c bundle.sha256
"$inventory_python" -c 'import json; from pathlib import Path; r=json.loads(Path("result.json").read_text()); assert r["status"]=="COMPLETE_METADATA_INVENTORY" and r["outcomes_not_read"] and not r["publication_result"]; assert not Path("failure.json").exists()'
