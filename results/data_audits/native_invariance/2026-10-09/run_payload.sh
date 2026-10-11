#!/usr/bin/env bash
set -euo pipefail
cd /scratch/igorno-alignssl_restart_20260922/native-cigar-invariance-20261009-01
fixture_python=/home/igorno/miniconda3/envs/truvari_env/bin/python
"$fixture_python" -c 'import sys, pysam, pytest, json; versions={"python":sys.version.split()[0],"pysam":pysam.__version__,"htslib":pysam.__samtools_version__,"pytest":pytest.__version__}; print(json.dumps(versions)); assert versions == {"python":"3.10.20","pysam":"0.24.0","htslib":"1.23.1","pytest":"8.4.2"}'
cd code
"$fixture_python" -m pytest -q -rA -p no:cacheprovider --basetemp ../control_tmp \
 tests/test_native_cigar_fixture.py tests/test_observe_native_fixture.py \
 tests/test_native_cigar_launcher.py tests/test_native_fixture_settings.py \
 tests/test_native_fixture_artifact_integrity.py \
 > ../controls.stdout.log 2> ../controls.stderr.log
tail -n 1 ../controls.stdout.log | grep -Eq '^70 passed(, [0-9]+ warnings?)? in [0-9.]+s$'
"$fixture_python" -c 'from analysis.run_native_cigar_fixture import tree_size; print("control_bytes", tree_size("../control_tmp",32*1024**2,max_files=4096,allow_test_links=True))'
cd ..
sha256sum -c bundle.sha256
"$fixture_python" code/analysis/run_native_cigar_fixture.py --root "$PWD"
sha256sum -c bundle.sha256
