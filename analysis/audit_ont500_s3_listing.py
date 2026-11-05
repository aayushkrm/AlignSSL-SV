#!/usr/bin/env python3
"""Inventory the public ONT-500 Sniffles prefix and match exact RNA titles."""

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import urllib.parse
import xml.etree.ElementTree as ET


PREFIX = "PROCESSED_DATA/ALIGNED_TO_HG38/SNIFFLES_v2.6.2/"
NS = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}
KEY = re.compile(re.escape(PREFIX) + r"((?:HG|GM|NA)\d{5})\.[^/]+_sniffles_v2\.6\.2\.vcf\.gz$")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cluster-helper", type=Path, required=True)
    p.add_argument("--crosswalk", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    crosswalk_bytes = a.crosswalk.read_bytes()
    crosswalk = json.loads(crosswalk_bytes)
    targets = {r["rna_sample_title"] for r in crosswalk["rows"] if r["ont500_exact_metadata_label"]}
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    objects, pages, token = [], [], None
    for index in range(10):
        params = {"list-type": "2", "prefix": PREFIX, "max-keys": "1000"}
        if token:
            params["continuation-token"] = token
        url = "https://s3.amazonaws.com/1000g-ont/?" + urllib.parse.urlencode(params)
        command = [str(a.cluster_helper.resolve()),
                   "curl --fail --silent --show-error --location --connect-timeout 8 "
                   "--max-time 25 --max-filesize 2097152 " + shlex.quote(url)]
        run = subprocess.run(command, capture_output=True, timeout=40)
        (out / f"page{index + 1:02}.stderr.txt").write_bytes(run.stderr)
        (out / f"page{index + 1:02}.xml").write_bytes(run.stdout)
        if run.returncode or len(run.stdout) > 2 * 1024 * 1024:
            raise ValueError("listing fetch failed; raw page retained")
        xml = ET.fromstring(run.stdout)
        if xml.findtext("s:Name", namespaces=NS) != "1000g-ont" or xml.findtext("s:Prefix", namespaces=NS) != PREFIX:
            raise ValueError("listing bucket or prefix mismatch")
        for child in xml.findall("s:Contents", NS):
            objects.append({"key": child.findtext("s:Key", namespaces=NS),
                            "size": int(child.findtext("s:Size", namespaces=NS)),
                            "etag": child.findtext("s:ETag", namespaces=NS),
                            "last_modified": child.findtext("s:LastModified", namespaces=NS)})
        truncated = xml.findtext("s:IsTruncated", namespaces=NS)
        pages.append({"url": url, "sha256": sha(run.stdout), "bytes": len(run.stdout),
                      "is_truncated": truncated, "argv": command})
        if truncated == "false":
            break
        if truncated != "true" or not (token := xml.findtext("s:NextContinuationToken", namespaces=NS)):
            raise ValueError("invalid pagination state")
    else:
        raise ValueError("listing exceeded ten-page budget")
    keys = {o["key"]: o for o in objects}
    if len(keys) != len(objects):
        raise ValueError("duplicate keys across listing pages")
    grouped = {sample: [] for sample in targets}
    for obj in objects:
        match = KEY.fullmatch(obj["key"])
        if match and match.group(1) in grouped:
            vcf = obj["key"]
            grouped[match.group(1)].append({"vcf": obj, "index": keys.get(vcf + ".csi")})
    rows = [{"rna_title": sample, "vcf_objects": grouped[sample]} for sample in sorted(targets)]
    summary = {"retrieved_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "prefix": PREFIX, "pages": pages, "object_count": len(objects),
               "target_count": len(targets), "targets_with_vcf": sum(bool(r["vcf_objects"]) for r in rows),
               "targets_with_exactly_one_vcf_and_csi": sum(len(r["vcf_objects"]) == 1 and r["vcf_objects"][0]["index"] is not None for r in rows),
               "rows": rows, "crosswalk_sha256": sha(crosswalk_bytes),
               "script_sha256": sha(Path(__file__).resolve().read_bytes()),
               "limits": "Object listings only. ETags are opaque; file bodies, identities, genotypes and usability were not verified."}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
