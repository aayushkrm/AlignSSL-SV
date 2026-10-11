#!/usr/bin/env bash
set -euo pipefail
cd /beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/svupp-inventory-20261009-01
inventory_python=/home/igorno/miniconda3/envs/truvari_env/bin/python
"$inventory_python" -c 'import sys, pytest, json; versions={"python":sys.version.split()[0],"pytest":pytest.__version__}; print(json.dumps(versions)); assert versions == {"python":"3.10.20","pytest":"8.4.2"}'
cd code
"$inventory_python" -m pytest -q -rA -p no:cacheprovider --basetemp ../control_tmp \
 tests/test_pinned_research_zip.py tests/test_svupp_archive_launcher.py \
 > ../controls.stdout.log 2> ../controls.stderr.log
tail -n 1 ../controls.stdout.log | grep -Eq '^28 passed(, [0-9]+ warnings?)? in [0-9.]+s$'
"$inventory_python" -c 'from analysis.run_svupp_archive_inventory import control_tree_size; print("control_bytes", control_tree_size("../control_tmp"))'
cd ..
sha256sum -c bundle.sha256
"$inventory_python" code/analysis/run_svupp_archive_inventory.py --root "$PWD"
sha256sum -c bundle.sha256
"$inventory_python" -c 'import json; from pathlib import Path; r=json.loads(Path("result.json").read_text()); assert r["status"]=="COMPLETE_METADATA_INVENTORY" and r["outcomes_not_read"] and not r["publication_result"]; assert not Path("failure.json").exists()'
