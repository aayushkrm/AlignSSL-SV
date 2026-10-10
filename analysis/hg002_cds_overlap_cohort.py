"""Development-only DNA CDS-overlap index; not a haplotype denominator or P1 test."""
import argparse, gzip, hashlib, json, re
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from pathlib import Path

MIN_SIZE = 50
PHASE_FIELDS = ("PS", "PID", "PGT", "HP")

def _open(path):
    path = Path(path)
    return gzip.open(path, "rt") if path.suffix == ".gz" else path.open()

def _attrs(text):
    result = {}
    for item in text.strip().rstrip(";").split(";"):
        parts = item.strip().split(None, 1)
        if len(parts) == 2: result[parts[0]] = parts[1].strip().strip('"')
    return result

def _read_gtf(path):
    by_chrom = defaultdict(list)
    with _open(path) as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip() or line.startswith("#"): continue
            f = line.rstrip("\n").split("\t")
            if len(f) != 9: raise ValueError(f"Malformed GTF line {line_no}")
            if f[2] != "CDS": continue
            start, end = int(f[3]) - 1, int(f[4])
            if start < 0 or end <= start: raise ValueError(f"Invalid CDS coordinates at line {line_no}")
            a = _attrs(f[8]); typ = a.get("gene_type", a.get("gene_biotype"))
            if typ and typ != "protein_coding": continue
            bio = typ or a.get("transcript_type", a.get("transcript_biotype"))
            gid, tid = a.get("gene_id"), a.get("transcript_id")
            known = bio == "protein_coding" and bool(gid and tid)
            by_chrom[f[0]].append((start, end, gid or f"UNKNOWN_GENE_LINE_{line_no}",
                a.get("gene_name"), tid or f"UNKNOWN_TRANSCRIPT_LINE_{line_no}", known))
    if not by_chrom: raise ValueError("GTF contains no CDS features")
    index = {}
    for chrom, items in by_chrom.items():
        items.sort(key=lambda x: (x[0], x[1], x[2], x[4])); prefix, high = [], -1
        for item in items: high = max(high, item[1]); prefix.append(high)
        index[chrom] = (items, [x[0] for x in items], prefix)
    return index

def _overlaps(index, start, end, boundary):
    items, starts, prefix = index
    if boundary is not None:
        lo, hi = bisect_left(prefix, boundary), bisect_right(starts, boundary)
        return [x for x in items[lo:hi] if x[0] <= boundary <= x[1]]
    lo, hi = bisect_right(prefix, start), bisect_left(starts, end)
    return [x for x in items[lo:hi] if x[0] < end and x[1] > start]

def _info(text):
    out = defaultdict(list)
    for item in text.split(";"):
        key, _, value = item.partition("=")
        if key and key != ".": out[key].append(value)
    return out

def _value(info, key, alt_i, n_alt, why, number=None):
    values = info.get(key, [])
    if not values: return None
    if len(values) != 1:
        why.append(key + "_duplicate_key"); return None
    parts = values[0].split(",")
    allowed = (1,) if number == "1" else (n_alt,) if number == "A" else (1, n_alt) if number in (None, ".") else ()
    if len(parts) not in allowed:
        why.append(key + "_ambiguous_cardinality"); return None
    value = parts[alt_i - 1] if len(parts) == n_alt else parts[0]
    return value if value not in ("", ".") else None

def _literal(ref, alt, pos):
    pre = 0
    while pre < min(len(ref), len(alt)) and ref[pre] == alt[pre]: pre += 1
    suf = 0
    while suf < min(len(ref) - pre, len(alt) - pre) and ref[-suf-1] == alt[-suf-1]: suf += 1
    r, a = ref[pre:len(ref)-suf], alt[pre:len(alt)-suf]
    point = pos - 1 + pre
    if r and not a: return "DEL", point, point + len(r), None, len(r)
    if a and not r: return "INS", None, None, point, len(a)
    return None

def _geometry(f, alt, info, alt_i, n_alt, numbers):
    pos, ref = int(f[1]), f[3]
    if pos < 1: raise ValueError("VCF POS must be positive")
    bad = []; values = {k: _value(info, k, alt_i, n_alt, bad, numbers.get(k)) for k in ("SVTYPE", "SVLEN", "END")}
    sym = re.fullmatch(r"<([^>]+)>", alt)
    literal = _literal(ref, alt, pos) if re.fullmatch("[ACGTNacgtn]+", ref + alt) else None
    symbolic_kind = sym.group(1).split(":")[0].upper() if sym else None
    kind = literal[0] if literal else symbolic_kind or (values["SVTYPE"] or "").upper()
    if kind not in {"DEL", "INS"}:
        if bad and any(re.search(r"\b(DEL|INS)\b", v) for v in info.get("SVTYPE", [])):
            return "UNKNOWN", None, None, None, None, bad + ["unresolved_SVTYPE"]
        return None
    declared = values["SVTYPE"]
    if declared and declared.upper() != kind: bad.append("SVTYPE_ALT_disagreement")
    numeric = {}
    for key in ("SVLEN", "END"):
        try: numeric[key] = int(values[key]) if values[key] is not None else None
        except ValueError: numeric[key] = None; bad.append(key + "_unparseable")
    size = abs(numeric["SVLEN"]) if numeric["SVLEN"] is not None else None
    end = numeric["END"]; why = ["symbolic_allele_sequence_unavailable"] if sym else []
    if literal:
        kind, start, stop, boundary, actual_size = literal
        if size is not None and size != actual_size: bad.append("SVLEN_disagrees_with_sequence")
        if kind == "DEL" and end is not None and end != stop: bad.append("END_disagrees_with_sequence")
        size = actual_size
    else:
        if not sym: why.append("complex_or_missing_allele_sequence")
        start, stop, boundary = (pos, end, None) if kind == "DEL" else (None, None, pos)
        if kind == "DEL" and end is not None:
            if end <= pos: bad.append("invalid_END")
            elif size is not None and size != end - pos: bad.append("END_SVLEN_disagreement")
            else: size = end - pos
        if kind == "DEL" and end is None and size is not None:
            stop = pos + size; why.append("missing_END_inferred_from_SVLEN")
        if size is None: why.append("missing_size")
        if kind == "DEL" and stop is None: why.append("missing_coordinates_and_size")
    if bad: start = stop = boundary = size = None
    return kind, start, stop, boundary, size, why + bad

def _call(format_keys, sample_text, alt_i, n_alt):
    values = dict(zip(format_keys, sample_text.split(":")))
    gt, phase = values.get("GT"), {k: values[k] for k in PHASE_FIELDS if k in values}
    tokens = re.split(r"[/|]", gt) if gt else []
    parsed = [int(x) for x in tokens if x.isdigit()]
    valid = bool(tokens) and all(x.isdigit() and int(x) <= n_alt for x in tokens)
    if valid and alt_i not in parsed: return None
    why = []
    if not gt: why.append("missing_GT")
    elif not valid: why.append("partial_or_invalid_GT")
    phased = bool(gt and "|" in gt and "/" not in gt)
    if len(set(parsed)) > 1 and not phased: why.append("unphased_GT")
    block = phase.get("PS") not in (None, ".") or phase.get("PID") not in (None, ".")
    if phased and len(set(parsed)) > 1 and not block: why.append("missing_phase_block")
    status = "UNKNOWN" if not valid else "PHASED" if phased else "UNPHASED"
    return {"GT": gt, "phase": phase, "why": why, "phase_status": status,
        "alt_copy_count": parsed.count(alt_i) if valid else None}

def build_manifest(vcf_path, gtf_path, sample, counters=None):
    """Return preliminary event/gene/ALT rows; counters count source ALT observations."""
    if not sample: raise ValueError("An explicit nonempty sample is required")
    cds, rows, samples, contigs, numbers = _read_gtf(gtf_path), {}, None, set(), {}
    counts = Counter({k: 0 for k in ("input_records", "input_alt_observations", "out_of_primary_uncalled_ALT",
        "out_of_primary_other_type", "out_of_primary_known_small", "out_of_primary_outside_CDS", "OVERLAPS_CDS", "UNKNOWN")})
    with _open(vcf_path) as stream:
        for line_no, line in enumerate(stream, 1):
            if line.startswith("##"):
                m = re.match(r"##INFO=<ID=([^,>]+),Number=([^,>]+)", line)
                if m: numbers[m[1]] = m[2]
                continue
            if line.startswith("#CHROM\t"):
                names = line.rstrip("\n").split("\t")[9:]
                if len(set(names)) != len(names) or sample not in names:
                    raise ValueError(f"Explicit sample {sample!r} is absent or duplicated")
                samples, sample_i = names, names.index(sample) + 9
                continue
            if line.startswith("#") or not line.strip(): continue
            if samples is None: raise ValueError("VCF #CHROM header is missing")
            f = line.rstrip("\n").split("\t")
            if len(f) < 10 or len(f) <= sample_i: raise ValueError(f"Malformed VCF line {line_no}")
            contigs.add(f[0]); counts["input_records"] += 1
            info, alts = _info(f[7]), f[4].split(","); fmt = f[8].split(":")
            for alt_i, alt in enumerate(alts, 1):
                counts["input_alt_observations"] += 1
                call = _call(fmt, f[sample_i], alt_i, len(alts))
                if call is None: counts["out_of_primary_uncalled_ALT"] += 1; continue
                geom = _geometry(f, alt, info, alt_i, len(alts), numbers)
                if geom is None: counts["out_of_primary_other_type"] += 1; continue
                kind, start, end, boundary, size, why = geom
                if size is not None and size < MIN_SIZE: counts["out_of_primary_known_small"] += 1; continue
                why += call["why"]
                if f[6] != "PASS": why.append("FILTER_" + ("missing" if f[6] == "." else "not_PASS"))
                localized = boundary is not None or (start is not None and end is not None)
                hits = _overlaps(cds[f[0]], start, end, boundary) if localized and f[0] in cds else []
                overlap = "OVERLAPS_CDS" if hits else "OUTSIDE_CDS" if localized and f[0] in cds else "UNKNOWN"
                if f[0] not in cds: why.append("contig_not_in_annotation")
                counts["out_of_primary_outside_CDS" if overlap == "OUTSIDE_CDS" else overlap] += 1
                genes = defaultdict(list)
                for hit in hits: genes[hit[2]].append(hit)
                if not genes: genes[None] = []
                identity = [f[0], f[1], f[3], alt, kind, start, end, boundary, size, f[7] if not localized else None]
                eid = hashlib.sha256(json.dumps(identity, separators=(",", ":")).encode()).hexdigest()[:20]
                for gid, features in genes.items():
                    row_why = why + (["gene_biotype_unknown"] if any(not x[5] for x in features) else [])
                    key = (eid, gid)
                    if key not in rows:
                        rows[key] = {"event_key": eid, "sample": sample, "chrom": f[0], "svtype": kind,
                            "start0": start, "end0": end, "insertion_boundary0": boundary, "size_bp": size,
                            "alternate": alt, "gene_id": gid, "gene_names": sorted({x[3] for x in features if x[3]}),
                            "transcripts": sorted({x[4] for x in features}), "source_records": [],
                            "index_role": "PRELIMINARY_EVENT_GENE_ALT", "p1_state": "NOT_ASSESSED",
                            "overlap_status": overlap, "unknown_reasons": []}
                    row = rows[key]; row["unknown_reasons"] = sorted(set(row["unknown_reasons"]) | set(row_why))
                    row["candidate_state"] = "UNKNOWN" if row["unknown_reasons"] or overlap == "UNKNOWN" else "OUTSIDE_PRIMARY" if overlap == "OUTSIDE_CDS" else "CANDIDATE"
                    row["source_records"].append({"record_id": f[2], "line": line_no, "POS": int(f[1]), "REF": f[3],
                        "FILTER": f[6], "GT": call["GT"], "phase": call["phase"], "phase_status": call["phase_status"],
                        "alt_copy_count": call["alt_copy_count"], "alt_index": alt_i, "INFO_raw": f[7]})
    if samples is None: raise ValueError("VCF #CHROM header is missing")
    if contigs and not contigs.intersection(cds): raise ValueError("VCF event contigs share no contigs with CDS annotation; no implicit renaming")
    counts["index_rows"] = len(rows)
    if counters is not None: counters.update(counts)
    return sorted(rows.values(), key=lambda x: (x["chrom"], x["start0"] or 0, x["event_key"], x["gene_id"] or ""))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("vcf", "gtf", "output"): parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--sample", required=True)
    args = parser.parse_args(); counters = {}; rows = build_manifest(args.vcf, args.gtf, args.sample, counters)
    summary = {"index_role": "PRELIMINARY_EVENT_GENE_ALT", "final_D": None, "counters": counters, "sample": args.sample}
    with args.output.open("x") as out:
        for row in [summary, *rows]: out.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))

if __name__ == "__main__":
    main()
