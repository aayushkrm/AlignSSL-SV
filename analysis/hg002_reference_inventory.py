#!/usr/bin/env python3
"""Reference-only streaming inventory for the pinned HG002 GENCODE GTF.

This reports annotation declarations. It does not inspect DNA/RNA sequence,
select transcripts, or classify the frozen P1 endpoint.
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import gzip
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


PINNED_SOURCE_SIZE = 4_688_772_094
PINNED_SOURCE_SHA256 = "04af7379ad6c214f49758db270938a38c41bebbf7b9dc8e24065d8f3a9f08d0d"
DEFAULT_DEADLINE_SECONDS = 900
DEFAULT_CHECKPOINT_SECONDS = 15
ISSUE_EXAMPLE_LIMIT = 100
HASH_CHUNK_BYTES = 4 * 1024 * 1024
PHASES = ("0", "1", "2")
TYPE_ATTRIBUTE_KEYS = (
    "gene_type",
    "gene_biotype",
    "transcript_type",
    "transcript_biotype",
)
IDENTITY_ATTRIBUTE_KEYS = {
    "gene_id",
    "transcript_id",
    "gene_name",
    "transcript_name",
    "gene_type",
    "gene_biotype",
    "transcript_type",
    "transcript_biotype",
    "ID",
    "Parent",
}


class InventoryError(Exception):
    """Base class for a run that must be preserved as incomplete."""


class DeadlineExpired(InventoryError):
    pass


class RunCancelled(InventoryError):
    pass


class SourceIdentityError(InventoryError):
    pass


class RunControl:
    def __init__(
        self,
        deadline_seconds: float,
        cancel_event: Any = None,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        self._monotonic = monotonic or time.monotonic
        self.started = self._monotonic()
        self.deadline = self.started + deadline_seconds
        self.cancel_event = cancel_event

    def check(self) -> None:
        if self.cancel_event is not None and self.cancel_event.is_set():
            raise RunCancelled("cancellation requested")
        if self._monotonic() >= self.deadline:
            raise DeadlineExpired("wall-clock deadline reached")

    def remaining(self) -> float:
        return max(0.0, self.deadline - self._monotonic())


class Fingerprint:
    """Order-independent multiset fingerprint for selected CDS index rows."""

    def __init__(self) -> None:
        self.count = 0
        self.digest_xor = 0
        self.digest_sum = 0

    def add(self, row: tuple[Any, ...]) -> None:
        payload = json.dumps(row, ensure_ascii=True, separators=(",", ":"))
        value = int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest(), "big")
        self.count += 1
        self.digest_xor ^= value
        self.digest_sum = (self.digest_sum + value) % (1 << 256)

    def to_json(self) -> dict[str, Any]:
        return {
            "row_count": self.count,
            "sha256_tuple_digest_xor": f"{self.digest_xor:064x}",
            "sha256_tuple_digest_sum_mod_2_256": f"{self.digest_sum:064x}",
        }


def _utc_now() -> str:
    return _datetime.datetime.now(_datetime.timezone.utc).isoformat()


def _stat_record(path: Path) -> dict[str, int]:
    st = path.stat()
    return {
        "device": int(st.st_dev),
        "inode": int(st.st_ino),
        "size_bytes": int(st.st_size),
        "mtime_ns": int(st.st_mtime_ns),
        "ctime_ns": int(st.st_ctime_ns),
    }


def _same_stat(*records: dict[str, int] | None) -> bool:
    present = [record for record in records if record is not None]
    return bool(present) and all(record == present[0] for record in present[1:])


def _hash_file(path: Path, control: RunControl) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            control.check()
            chunk = stream.read(HASH_CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _open_gtf(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return path.open("rt", encoding="utf-8", newline="")


def _split_attribute_items(text: str) -> tuple[list[str], list[str]]:
    items: list[str] = []
    problems: list[str] = []
    start = 0
    quoted = False
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quoted:
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif char == ";" and not quoted:
            items.append(text[start:index].strip())
            start = index + 1
    if quoted:
        problems.append("unclosed_attribute_quote")
    tail = text[start:].strip()
    if tail:
        items.append(tail)
    return items, problems


def _decode_attribute_value(raw: str) -> tuple[str, list[str]]:
    raw = raw.strip()
    if not raw:
        return "", ["empty_attribute_value"]
    if raw[0] != '"':
        return raw, ["unquoted_attribute_value"]
    escaped = False
    closing = None
    for index in range(1, len(raw)):
        char = raw[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            closing = index
            break
    if closing is None:
        return raw[1:], ["unclosed_attribute_value"]
    tail = raw[closing + 1 :].strip()
    value = raw[1:closing].replace('\\"', '"').replace("\\\\", "\\")
    problems = ["trailing_attribute_text"] if tail else []
    return value, problems


def parse_attributes(text: str) -> tuple[dict[str, list[str]], list[str]]:
    """Parse GTF attributes without collapsing repeated keys or values."""
    result: dict[str, list[str]] = defaultdict(list)
    if not text.strip():
        return {}, ["empty_attribute_column"]
    items, problems = _split_attribute_items(text.strip().rstrip(";"))
    for item in items:
        if not item:
            continue
        match = re.match(r"^([^\s=]+)\s+(.*)$", item, flags=re.DOTALL)
        if not match:
            problems.append("attribute_missing_key_or_value")
            continue
        key, raw_value = match.groups()
        value, value_problems = _decode_attribute_value(raw_value)
        result[key].append(value)
        problems.extend(f"{key}:{problem}" for problem in value_problems)
    return dict(result), problems


def _legacy_attributes(text: str) -> dict[str, str]:
    """Mirror the existing cohort index's _attrs parsing for its filter only."""
    result: dict[str, str] = {}
    for item in text.strip().rstrip(";").split(";"):
        parts = item.strip().split(None, 1)
        if len(parts) == 2:
            result[parts[0]] = parts[1].strip().strip('"')
    return result


def _ids(attributes: dict[str, list[str]], key: str) -> list[str]:
    return sorted({value for value in attributes.get(key, []) if value})


def _new_entity() -> list[set[str]]:
    return [set() for _ in range(6)]


class InventoryState:
    def __init__(self) -> None:
        self.counters: Counter[str] = Counter()
        self.feature_type_counts: Counter[str] = Counter()
        self.issue_counts: Counter[str] = Counter()
        self.issue_examples: list[dict[str, Any]] = []
        self.attribute_rows_by_feature: dict[str, Counter[str]] = defaultdict(Counter)
        self.identifier_presence_by_feature: dict[str, Counter[str]] = defaultdict(Counter)
        self.identifier_missing_by_feature: dict[str, Counter[str]] = defaultdict(Counter)
        self.duplicate_attribute_rows: Counter[str] = Counter()
        self.conflicting_attribute_rows: Counter[str] = Counter()
        self.source_type_value_counts: dict[str, Counter[str]] = {
            key: Counter() for key in TYPE_ATTRIBUTE_KEYS
        }
        self.tag_value_counts: Counter[str] = Counter()
        self.tag_rows_by_feature: dict[str, Counter[str]] = defaultdict(Counter)
        self.transcript_tags: dict[str, set[str]] = defaultdict(set)
        self.tag_rows_without_transcript_id: Counter[str] = Counter()
        self.codon_rows: Counter[str] = Counter()
        self.codon_bases: Counter[str] = Counter()
        self.codon_valid_span_rows: Counter[str] = Counter()
        self.codon_unavailable_span_rows: Counter[str] = Counter()
        self.codon_bases_by_strand: dict[str, Counter[str]] = defaultdict(Counter)
        self.codon_transcript_bases: dict[str, dict[str, list[int]]] = {
            "start_codon": {},
            "stop_codon": {},
        }
        self.transl_except_attribute_occurrences = 0
        self.transl_except_feature_rows = 0
        self.transl_except_aa_counts: Counter[str] = Counter()
        self.transl_except_rows_by_feature: Counter[str] = Counter()
        self.transl_except_sec_occurrences = 0
        self.selenocysteine_feature_rows: Counter[str] = Counter()
        self.selenocysteine_feature_bases: Counter[str] = Counter()
        self.selenocysteine_tag_values: Counter[str] = Counter()
        self.gene_meta: dict[str, list[set[str]]] = {}
        self.transcript_meta: dict[str, list[set[str]]] = {}
        self.feature_id_meta: dict[str, list[set[str]]] = {}
        self.cds_gene_ids: set[str] = set()
        self.cds_transcript_ids: set[str] = set()
        self.cds_phase_counts: Counter[str] = Counter({**{p: 0 for p in PHASES}, "malformed": 0})
        self.cds_phase_malformed_values: Counter[str] = Counter()
        self.cds_bases_by_phase: Counter[str] = Counter()
        self.cds_bases = 0
        self.cds_valid_coordinate_rows = 0
        self.cds_transcript_meta: dict[str, list[int]] = {}
        self.transcript_tag_id_counts: Counter[str] = Counter()
        self.index_candidate_cds_rows = 0
        self.index_selected_rows = 0
        self.index_biotype_excluded_rows = 0
        self.index_selected_unknown_biotype_rows = 0
        self.index_fingerprint = Fingerprint()
        self.eof_reached = False
        self.last_line_number = 0
        self.unique_gene_ids_checkpoint: int | None = None
        self.unique_transcript_ids_checkpoint: int | None = None

    def issue(self, code: str, line_number: int, feature_type: str | None = None) -> None:
        self.issue_counts[code] += 1
        if len(self.issue_examples) < ISSUE_EXAMPLE_LIMIT:
            example: dict[str, Any] = {"line": line_number, "issue": code}
            if feature_type is not None:
                example["feature_type"] = feature_type
            self.issue_examples.append(example)

    def _entity(self, store: dict[str, list[set[str]]], ident: str) -> list[set[str]]:
        value = store.get(ident)
        if value is None:
            value = _new_entity()
            store[ident] = value
        return value

    def _count_cds_phase(self, fields: list[str], line_number: int) -> None:
        phase = fields[7] if len(fields) > 7 else ""
        if phase in PHASES:
            self.cds_phase_counts[phase] += 1
        else:
            self.cds_phase_counts["malformed"] += 1
            label = "missing" if phase == "" else "dot" if phase == "." else phase
            self.cds_phase_malformed_values[label] += 1
            if phase not in ("", "."):
                self.issue("malformed_CDS_phase", line_number, "CDS")

    def _count_index_selection(
        self,
        chrom: str,
        start0: int,
        end0: int,
        attributes_text: str,
        line_number: int,
    ) -> None:
        self.index_candidate_cds_rows += 1
        attributes = _legacy_attributes(attributes_text)
        gene_type = attributes.get("gene_type", attributes.get("gene_biotype"))
        if gene_type and gene_type != "protein_coding":
            self.index_biotype_excluded_rows += 1
            return
        transcript_type = gene_type or attributes.get(
            "transcript_type", attributes.get("transcript_biotype")
        )
        gene_id = attributes.get("gene_id")
        transcript_id = attributes.get("transcript_id")
        known = transcript_type == "protein_coding" and bool(gene_id and transcript_id)
        gene_name = attributes.get("gene_name")
        row = (
            chrom,
            start0,
            end0,
            gene_id or f"UNKNOWN_GENE_LINE_{line_number}",
            gene_name,
            transcript_id or f"UNKNOWN_TRANSCRIPT_LINE_{line_number}",
            known,
        )
        self.index_selected_rows += 1
        if not transcript_type:
            self.index_selected_unknown_biotype_rows += 1
        self.index_fingerprint.add(row)

    def consume(self, line: str, line_number: int) -> None:
        self.last_line_number = line_number
        self.counters["physical_lines"] += 1
        if not line.strip():
            self.counters["blank_lines"] += 1
            return
        if line.startswith("#"):
            self.counters["comment_lines"] += 1
            return

        fields = line.rstrip("\r\n").split("\t")
        feature_type: str | None = None
        if len(fields) > 2:
            feature_type = fields[2] or "(empty)"
            self.feature_type_counts[feature_type] += 1
            self.counters["rows_with_feature_type_column"] += 1
        else:
            self.counters["rows_without_feature_type_column"] += 1

        if feature_type == "CDS":
            self.counters["CDS_feature_rows"] += 1
            self._count_cds_phase(fields, line_number)
        if feature_type in ("start_codon", "stop_codon"):
            self.codon_rows[feature_type] += 1
        if len(fields) != 9:
            self.counters["malformed_column_count_rows"] += 1
            self.issue("column_count_not_9", line_number, feature_type)
            return

        self.counters["nine_column_feature_rows"] += 1
        chrom, strand = fields[0], fields[6]
        try:
            start1, end1 = int(fields[3]), int(fields[4])
            if start1 < 1 or end1 < start1:
                raise ValueError("start/end outside valid GTF interval")
            valid_coordinates = True
            self.counters["valid_coordinate_feature_rows"] += 1
            span = end1 - start1 + 1
        except (ValueError, OverflowError):
            start1 = end1 = span = 0
            valid_coordinates = False
            self.counters["invalid_coordinate_feature_rows"] += 1
            self.issue("invalid_GTF_coordinates", line_number, feature_type)

        attributes, attribute_problems = parse_attributes(fields[8])
        if attribute_problems:
            self.counters["malformed_attribute_rows"] += 1
            for problem in set(attribute_problems):
                self.issue("malformed_attribute:" + problem, line_number, feature_type)
        for key, values in attributes.items():
            self.attribute_rows_by_feature[feature_type or "(unknown)"][key] += 1
            if len(values) > 1:
                self.duplicate_attribute_rows[key] += 1
                if len(set(values)) > 1:
                    self.conflicting_attribute_rows[key] += 1
                    if key in IDENTITY_ATTRIBUTE_KEYS:
                        self.issue("conflicting_duplicate_attribute:" + key, line_number, feature_type)
        for key in ("gene_id", "transcript_id", "ID", "Parent"):
            if _ids(attributes, key):
                self.identifier_presence_by_feature[feature_type or "(unknown)"][key] += 1
            else:
                self.identifier_missing_by_feature[feature_type or "(unknown)"][key] += 1
        if not _ids(attributes, "gene_id"):
            self.counters["valid_width_rows_missing_gene_id"] += 1
            self.issue("missing_gene_id", line_number, feature_type)
        if feature_type != "gene" and not _ids(attributes, "transcript_id"):
            self.counters["valid_width_rows_missing_transcript_id"] += 1
            self.issue("missing_transcript_id", line_number, feature_type)
        for key in TYPE_ATTRIBUTE_KEYS:
            self.source_type_value_counts[key].update(attributes.get(key, []))

        gene_ids = _ids(attributes, "gene_id")
        transcript_ids = _ids(attributes, "transcript_id")
        for gene_id in gene_ids:
            meta = self._entity(self.gene_meta, gene_id)
            meta[0].add(chrom)
            meta[1].add(strand)
            meta[2].update(attributes.get("gene_type", []))
            meta[2].update(attributes.get("gene_biotype", []))
            meta[3].update(_ids(attributes, "gene_name"))
            if feature_type == "gene":
                meta[5].add("gene")
        for transcript_id in transcript_ids:
            meta = self._entity(self.transcript_meta, transcript_id)
            meta[0].add(chrom)
            meta[1].add(strand)
            meta[2].update(attributes.get("transcript_type", []))
            meta[2].update(attributes.get("transcript_biotype", []))
            meta[4].update(_ids(attributes, "transcript_name"))
            if feature_type in ("transcript", "mRNA"):
                meta[5].add(feature_type)
            meta[3].update(gene_ids)
        for gene_id in gene_ids:
            self.gene_meta[gene_id][4].update(transcript_ids)

        parent_ids = _ids(attributes, "Parent")
        for feature_id in _ids(attributes, "ID"):
            meta = self.feature_id_meta.get(feature_id)
            if meta is None:
                meta = [set() for _ in range(4)]
                self.feature_id_meta[feature_id] = meta
            meta[0].add(feature_type or "(unknown)")
            meta[1].add(chrom)
            meta[2].add(strand)
            meta[3].update(parent_ids)

        if feature_type == "CDS":
            self.cds_gene_ids.update(gene_ids)
            self.cds_transcript_ids.update(transcript_ids)
            if valid_coordinates:
                self.cds_valid_coordinate_rows += 1
                self.cds_bases += span
                phase = fields[7] if fields[7] in PHASES else "malformed"
                self.cds_bases_by_phase[phase] += span
                for transcript_id in transcript_ids:
                    tx = self.cds_transcript_meta.setdefault(transcript_id, [0, 0, 0, 0])
                    tx[0] += span
                    tx[1] += 1
                    tx[2 if phase in PHASES else 3] += 1
            if valid_coordinates:
                self._count_index_selection(chrom, start1 - 1, end1, fields[8], line_number)

        if feature_type in ("start_codon", "stop_codon"):
            if valid_coordinates:
                self.codon_valid_span_rows[feature_type] += 1
                self.codon_bases[feature_type] += span
                strand_key = strand if strand in ("+", "-") else "other"
                self.codon_bases_by_strand[feature_type][strand_key] += span
                for transcript_id in transcript_ids:
                    by_tx = self.codon_transcript_bases[feature_type].setdefault(
                        transcript_id, [0, 0, 0]
                    )
                    by_tx[0] += span
                    by_tx[1] += 1
            else:
                self.codon_unavailable_span_rows[feature_type] += 1

        if "tag" in attributes:
            for tag in attributes["tag"]:
                self.tag_value_counts[tag] += 1
                self.tag_rows_by_feature[feature_type or "(unknown)"][tag] += 1
                if "selenocysteine" in tag.casefold():
                    self.selenocysteine_tag_values[tag] += 1
                if transcript_ids:
                    for transcript_id in transcript_ids:
                        tags = self.transcript_tags[transcript_id]
                        if tag not in tags:
                            tags.add(tag)
                            self.transcript_tag_id_counts[tag] += 1
                else:
                    self.tag_rows_without_transcript_id[tag] += 1

        if "transl_except" in attributes:
            self.transl_except_attribute_occurrences += len(attributes["transl_except"])
            self.transl_except_feature_rows += 1
            self.transl_except_rows_by_feature[feature_type or "(unknown)"] += 1
            for value in attributes["transl_except"]:
                match = re.search(r"(?:^|[,(:])\s*aa\s*:\s*([^,)\s]+)", value, flags=re.I)
                if match:
                    amino_acid = match.group(1)
                    self.transl_except_aa_counts[amino_acid] += 1
                    if amino_acid.casefold() in ("sec", "u"):
                        self.transl_except_sec_occurrences += 1

        if feature_type and "selenocysteine" in feature_type.casefold():
            self.selenocysteine_feature_rows[feature_type] += 1
            if valid_coordinates:
                self.selenocysteine_feature_bases[feature_type] += span

    def observed_payload(self, reason: str, derived_summary_status: str) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "scope": {
                "status": "INCOMPLETE",
                "counts_scope": "OBSERVED_PREFIX",
                "counts_complete": False,
                "eof_reached": self.eof_reached,
                "reason": reason,
                "derived_summary_status": derived_summary_status,
                "last_line_number": self.last_line_number,
            },
            "observed_counts": dict(sorted(self.counters.items())),
            "observed_feature_type_counts": dict(sorted(self.feature_type_counts.items())),
            "observed_source_type_attribute_value_counts": {
                key: dict(sorted(counter.items()))
                for key, counter in sorted(self.source_type_value_counts.items())
            },
            "observed_identifier_presence_by_feature_type": {
                feature_type: dict(sorted(counts.items()))
                for feature_type, counts in sorted(self.identifier_presence_by_feature.items())
            },
            "observed_identifier_missing_by_feature_type": {
                feature_type: dict(sorted(counts.items()))
                for feature_type, counts in sorted(self.identifier_missing_by_feature.items())
            },
            "observed_CDS_phase_counts": dict(sorted(self.cds_phase_counts.items())),
            "observed_CDS_phase_malformed_value_counts": dict(
                sorted(self.cds_phase_malformed_values.items())
            ),
            "observed_CDS_bases_by_phase": dict(sorted(self.cds_bases_by_phase.items())),
            "observed_CDS_annotated_base_sum": self.cds_bases,
            "observed_tag_value_counts": dict(sorted(self.tag_value_counts.items())),
            "observed_transcript_ids_with_cds_start_NF": self.transcript_tag_id_counts[
                "cds_start_NF"
            ],
            "observed_transcript_ids_with_cds_end_NF": self.transcript_tag_id_counts[
                "cds_end_NF"
            ],
            "observed_declared_codon_features": {
                codon: {
                    "feature_rows": self.codon_rows[codon],
                    "coordinate_valid_feature_rows": self.codon_valid_span_rows[codon],
                    "coordinate_invalid_or_unavailable_feature_rows": self.codon_unavailable_span_rows[codon],
                    "total_annotated_bases_sum_over_coordinate_blocks": self.codon_bases[codon],
                    "bases_by_strand": dict(sorted(self.codon_bases_by_strand[codon].items())),
                    "transcript_ids_with_valid_blocks": len(
                        self.codon_transcript_bases[codon]
                    ),
                }
                for codon in ("start_codon", "stop_codon")
            },
            "observed_transl_except": {
                "attribute_occurrences": self.transl_except_attribute_occurrences,
                "feature_rows": self.transl_except_feature_rows,
                "amino_acid_value_counts": dict(sorted(self.transl_except_aa_counts.items())),
                "Sec_or_U_occurrences": self.transl_except_sec_occurrences,
                "selenocysteine_feature_rows": dict(sorted(self.selenocysteine_feature_rows.items())),
                "selenocysteine_tag_values": dict(sorted(self.selenocysteine_tag_values.items())),
            },
            "observed_existing_cohort_index_selection_prediction": {
                "source_CDS_rows_with_valid_coordinates": self.index_candidate_cds_rows,
                "selected_rows_by_existing_filter": self.index_selected_rows,
                "excluded_by_existing_gene_type_filter": self.index_biotype_excluded_rows,
                "selected_row_multiset_fingerprint": self.index_fingerprint.to_json(),
            },
            "observed_unique_gene_ids": (
                self.unique_gene_ids_checkpoint
                if self.unique_gene_ids_checkpoint is not None
                else len(self.gene_meta)
            ),
            "observed_unique_transcript_ids": (
                self.unique_transcript_ids_checkpoint
                if self.unique_transcript_ids_checkpoint is not None
                else len(self.transcript_meta)
            ),
            "observed_issue_counts": dict(sorted(self.issue_counts.items())),
            "issue_examples_first_100": self.issue_examples,
        }

    def _type_counts_by_id(
        self,
        metadata: dict[str, list[set[str]]],
        type_index: int,
        cds_ids: set[str],
        guard: RunControl,
    ) -> tuple[Counter[str], dict[str, int]]:
        result: Counter[str] = Counter()
        protein_coding = {"total_unique_ids": 0, "with_CDS": 0}
        for count, (ident, values) in enumerate(metadata.items(), 1):
            if count % 8192 == 0:
                guard.check()
            declared = values[type_index]
            label = next(iter(declared)) if len(declared) == 1 else (
                "CONFLICTING_DECLARATIONS" if declared else "MISSING"
            )
            result[label] += 1
            if label == "protein_coding":
                protein_coding["total_unique_ids"] += 1
                if ident in cds_ids:
                    protein_coding["with_CDS"] += 1
        return result, protein_coding

    def _conflicts(
        self,
        metadata: dict[str, list[set[str]]],
        axes: dict[str, int],
        guard: RunControl,
    ) -> tuple[dict[str, int], list[dict[str, Any]]]:
        counts: Counter[str] = Counter()
        examples: list[dict[str, Any]] = []
        for ident_index, (ident, values) in enumerate(metadata.items(), 1):
            if ident_index % 8192 == 0:
                guard.check()
            conflicts = [name for name, index in axes.items() if len(values[index]) > 1]
            if not conflicts:
                continue
            for name in conflicts:
                counts[name] += 1
            if len(examples) < ISSUE_EXAMPLE_LIMIT:
                examples.append(
                    {
                        "id": ident,
                        "conflicts": conflicts,
                        "observed": {
                            name: sorted(values[index]) for name, index in axes.items()
                        },
                    }
                )
        return dict(sorted(counts.items())), examples

    def _codon_summary(self, codon: str) -> dict[str, Any]:
        per_transcript = self.codon_transcript_bases[codon]
        base_sum_counts: Counter[str] = Counter()
        block_counts: Counter[str] = Counter()
        for bases, blocks, _ in per_transcript.values():
            base_sum_counts[str(bases)] += 1
            block_counts["one_block" if blocks == 1 else "multiple_blocks"] += 1
        return {
            "feature_rows": self.codon_rows[codon],
            "coordinate_valid_feature_rows": self.codon_valid_span_rows[codon],
            "coordinate_invalid_or_unavailable_feature_rows": self.codon_unavailable_span_rows[codon],
            "total_annotated_bases_sum_over_coordinate_blocks": self.codon_bases[codon],
            "bases_by_strand": dict(sorted(self.codon_bases_by_strand[codon].items())),
            "transcript_ids_with_valid_coordinate_blocks": len(per_transcript),
            "transcript_block_count_classes": dict(sorted(block_counts.items())),
            "transcript_base_sum_distribution": dict(sorted(base_sum_counts.items())),
            "transcripts_with_observed_base_sum_of_3": base_sum_counts["3"],
            "interpretation": (
                "Sum of declared GTF coordinate-block lengths per transcript; split blocks "
                "are summed across junctions. Three annotated bases do not establish a "
                "sequence-confirmed or complete start/stop codon."
            ),
        }

    def summary(self, guard: RunControl) -> dict[str, Any]:
        gene_types, pc_genes = self._type_counts_by_id(
            self.gene_meta, 2, self.cds_gene_ids, guard
        )
        transcript_types, pc_transcripts = self._type_counts_by_id(
            self.transcript_meta, 2, self.cds_transcript_ids, guard
        )
        gene_conflicts, gene_examples = self._conflicts(
            self.gene_meta,
            {
                "multiple_contigs": 0,
                "multiple_strands": 1,
                "multiple_declared_types": 2,
                "multiple_gene_names": 3,
            },
            guard,
        )
        transcript_conflicts, transcript_examples = self._conflicts(
            self.transcript_meta,
            {
                "multiple_contigs": 0,
                "multiple_strands": 1,
                "multiple_declared_types": 2,
                "multiple_gene_ids": 3,
                "multiple_transcript_names": 4,
            },
            guard,
        )
        feature_id_conflicts, feature_id_examples = self._conflicts(
            self.feature_id_meta,
            {
                "multiple_feature_types": 0,
                "multiple_contigs": 1,
                "multiple_strands": 2,
                "multiple_parent_ids": 3,
            },
            guard,
        )
        pc_genes["without_CDS"] = (
            pc_genes["total_unique_ids"] - pc_genes["with_CDS"]
            if self.eof_reached
            else None
        )
        pc_transcripts["without_CDS"] = (
            pc_transcripts["total_unique_ids"] - pc_transcripts["with_CDS"]
            if self.eof_reached
            else None
        )
        for record in (pc_genes, pc_transcripts):
            record["CDS_membership_scope"] = (
                "FULL_SOURCE_EOF" if self.eof_reached else "OBSERVED_PREFIX; no-CDS is undetermined"
            )
            record["CDS_membership_complete"] = bool(
                self.eof_reached
                and self.counters["malformed_column_count_rows"] == 0
                and self.counters["malformed_attribute_rows"] == 0
                and self.counters["valid_width_rows_missing_gene_id"] == 0
                and self.counters["valid_width_rows_missing_transcript_id"] == 0
            )

        phase_status_counts: Counter[str] = Counter()
        transcript_length_mod3: Counter[str] = Counter()
        transcript_cds_base_sum = 0
        for count, (transcript_id, values) in enumerate(self.cds_transcript_meta.items(), 1):
            if count % 8192 == 0:
                guard.check()
            bases, _blocks, valid_phases, malformed_phases = values
            transcript_cds_base_sum += bases
            transcript_length_mod3[str(bases % 3)] += 1
            if valid_phases and malformed_phases:
                status = "MIXED_VALID_AND_MALFORMED"
            elif valid_phases:
                status = "ALL_VALID"
            elif malformed_phases:
                status = "ALL_MALFORMED"
            else:
                status = "NO_PHASE_ROWS"
            phase_status_counts[status] += 1

        start_nf = self.transcript_tag_id_counts["cds_start_NF"]
        end_nf = self.transcript_tag_id_counts["cds_end_NF"]
        malformed_semantics = (
            self.counters["malformed_column_count_rows"] > 0
            or self.counters["malformed_attribute_rows"] > 0
        )
        return {
            "schema_version": 1,
            "scope": {
                "status": "COMPLETE" if self.eof_reached else "INCOMPLETE",
                "counts_scope": "FULL_SOURCE_EOF" if self.eof_reached else "OBSERVED_PREFIX",
                "counts_complete": self.eof_reached,
                "eof_reached": self.eof_reached,
                "last_line_number": self.last_line_number,
                "semantic_metadata_has_parse_or_id_issues": bool(
                    malformed_semantics
                    or self.counters["valid_width_rows_missing_gene_id"]
                    or self.counters["valid_width_rows_missing_transcript_id"]
                ),
                "no_CDS_counts_are_observed_full_EOF_counts": self.eof_reached,
                "no_CDS_counts_are_unavailable_without_full_EOF": not self.eof_reached,
            },
            "counts": dict(sorted(self.counters.items())),
            "feature_type_counts": dict(sorted(self.feature_type_counts.items())),
            "source_declared_type_attribute_value_counts": {
                key: dict(sorted(counter.items()))
                for key, counter in sorted(self.source_type_value_counts.items())
            },
            "identifier_attribute_presence_by_feature_type": {
                feature_type: dict(sorted(counts.items()))
                for feature_type, counts in sorted(self.identifier_presence_by_feature.items())
            },
            "identifier_attribute_missing_by_feature_type": {
                feature_type: dict(sorted(counts.items()))
                for feature_type, counts in sorted(self.identifier_missing_by_feature.items())
            },
            "source_unique_gene_ids_by_declared_type": dict(sorted(gene_types.items())),
            "source_unique_transcript_ids_by_declared_type": dict(
                sorted(transcript_types.items())
            ),
            "protein_coding_gene_CDS_status": pc_genes,
            "protein_coding_transcript_CDS_status": pc_transcripts,
            "tags": {
                "source_tag_attribute_value_occurrences": dict(sorted(self.tag_value_counts.items())),
                "source_transcript_ids_with_cds_start_NF": start_nf,
                "source_transcript_ids_with_cds_end_NF": end_nf,
                "tag_rows_without_transcript_id": dict(sorted(self.tag_rows_without_transcript_id.items())),
                "tag_occurrences_by_feature_type": {
                    feature_type: dict(sorted(counts.items()))
                    for feature_type, counts in sorted(self.tag_rows_by_feature.items())
                },
            },
            "declared_codon_features": {
                codon: self._codon_summary(codon)
                for codon in ("start_codon", "stop_codon")
            },
            "CDS": {
                "feature_rows": self.counters["CDS_feature_rows"],
                "valid_coordinate_feature_rows": self.cds_valid_coordinate_rows,
                "annotated_base_sum_over_feature_rows": self.cds_bases,
                "phase_counts": dict(sorted(self.cds_phase_counts.items())),
                "malformed_phase_value_counts": dict(sorted(self.cds_phase_malformed_values.items())),
                "annotated_bases_by_phase": dict(sorted(self.cds_bases_by_phase.items())),
                "transcript_ids_with_CDS_feature_rows": len(self.cds_transcript_ids),
                "gene_ids_with_CDS_feature_rows": len(self.cds_gene_ids),
                "transcript_ids_with_valid_coordinate_CDS_rows": len(self.cds_transcript_meta),
                "transcript_annotated_base_sum": transcript_cds_base_sum,
                "transcript_annotated_length_mod_3_counts": dict(
                    sorted(transcript_length_mod3.items())
                ),
                "transcript_phase_annotation_status_counts": dict(
                    sorted(phase_status_counts.items())
                ),
                "frame_limit": (
                    "Length and declared GTF phase summaries only. No phase propagation, "
                    "DNA translation, functional-CDS completeness, or endpoint status is inferred."
                ),
            },
            "selenocysteine_and_transl_except": {
                "transl_except_attribute_occurrences": self.transl_except_attribute_occurrences,
                "feature_rows_with_transl_except": self.transl_except_feature_rows,
                "transl_except_rows_by_feature_type": dict(sorted(self.transl_except_rows_by_feature.items())),
                "transl_except_amino_acid_value_counts": dict(sorted(self.transl_except_aa_counts.items())),
                "transl_except_Sec_or_U_occurrences": self.transl_except_sec_occurrences,
                "selenocysteine_feature_rows_by_type": dict(sorted(self.selenocysteine_feature_rows.items())),
                "selenocysteine_feature_bases_by_type": dict(sorted(self.selenocysteine_feature_bases.items())),
                "selenocysteine_related_tag_occurrences": dict(sorted(self.selenocysteine_tag_values.items())),
                "interpretation": "Source annotation evidence only; no codon or translation is sequence-validated.",
            },
            "identifier_and_location_conflicts": {
                "gene_id_conflict_counts": gene_conflicts,
                "gene_id_conflict_examples_first_100": gene_examples,
                "transcript_id_conflict_counts": transcript_conflicts,
                "transcript_id_conflict_examples_first_100": transcript_examples,
                "feature_ID_attribute_conflict_counts": feature_id_conflicts,
                "feature_ID_attribute_conflict_examples_first_100": feature_id_examples,
                "gene_ids_without_gene_feature_rows": sum(
                    not values[5] for values in self.gene_meta.values()
                ),
                "transcript_ids_without_transcript_feature_rows": sum(
                    not values[5] for values in self.transcript_meta.values()
                ),
                "transcript_ids_without_gene_id_links": sum(
                    not values[3] for values in self.transcript_meta.values()
                ),
                "gene_transcript_string_id_collisions": len(
                    self.gene_meta.keys() & self.transcript_meta.keys()
                ),
                "duplicate_attribute_key_row_counts": dict(sorted(self.duplicate_attribute_rows.items())),
                "conflicting_duplicate_attribute_value_row_counts": dict(
                    sorted(self.conflicting_attribute_rows.items())
                ),
                "issue_counts": dict(sorted(self.issue_counts.items())),
                "issue_examples_first_100": self.issue_examples,
            },
            "existing_cohort_index_selection_prediction": {
                "index_source_CDS_rows_with_valid_coordinates": self.index_candidate_cds_rows,
                "selected_rows_by_existing_filter": self.index_selected_rows,
                "excluded_by_existing_gene_type_filter": self.index_biotype_excluded_rows,
                "selected_rows_without_effective_biotype": self.index_selected_unknown_biotype_rows,
                "selected_row_multiset_fingerprint": self.index_fingerprint.to_json(),
                "selection_rule": (
                    "Prediction from the current cohort _read_gtf parser/filter: CDS rows only; "
                    "exclude only a truthy gene_type-or-gene_biotype other than protein_coding; "
                    "then compute known from the existing gene/transcript type and ID expression."
                ),
            },
        }

    def release_metadata_for_index_probe(self) -> None:
        """Drop per-ID state before measuring the memory-heavy existing index."""
        self.unique_gene_ids_checkpoint = len(self.gene_meta)
        self.unique_transcript_ids_checkpoint = len(self.transcript_meta)
        self.gene_meta.clear()
        self.transcript_meta.clear()
        self.feature_id_meta.clear()
        self.cds_gene_ids.clear()
        self.cds_transcript_ids.clear()
        self.cds_transcript_meta.clear()
        self.transcript_tags.clear()
        for by_transcript in self.codon_transcript_bases.values():
            by_transcript.clear()


_INDEX_PROBE = r'''\
import hashlib, json, resource, sys, time
sys.path.insert(0, sys.argv[2])
from analysis.hg002_cds_overlap_cohort import _read_gtf

def fingerprint(index):
    count = 0
    value_xor = 0
    value_sum = 0
    for chrom in sorted(index):
        items, _starts, _prefix = index[chrom]
        for start, end, gene_id, gene_name, transcript_id, known in items:
            row = (chrom, start, end, gene_id, gene_name, transcript_id, known)
            payload = json.dumps(row, ensure_ascii=True, separators=(",", ":"))
            value = int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest(), "big")
            count += 1
            value_xor ^= value
            value_sum = (value_sum + value) % (1 << 256)
    return {
        "row_count": count,
        "sha256_tuple_digest_xor": f"{value_xor:064x}",
        "sha256_tuple_digest_sum_mod_2_256": f"{value_sum:064x}",
    }

try:
    wall0 = time.perf_counter()
    cpu0 = time.process_time()
    index = _read_gtf(sys.argv[1])
    build_wall = time.perf_counter() - wall0
    build_cpu = time.process_time() - cpu0
    fp0 = time.perf_counter()
    selected = fingerprint(index)
    fingerprint_wall = time.perf_counter() - fp0
    raw_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss_bytes = int(raw_rss if sys.platform == "darwin" else raw_rss * 1024)
    print(json.dumps({
        "ok": True,
        "existing_index_build_wall_seconds": build_wall,
        "existing_index_build_cpu_seconds": build_cpu,
        "actual_index_selection_fingerprint_wall_seconds": fingerprint_wall,
        "index_process_peak_rss_bytes": rss_bytes,
        "actual_index_selection": selected,
    }, sort_keys=True))
except BaseException as exc:
    print(json.dumps({"ok": False, "error_type": type(exc).__name__, "error": str(exc)}, sort_keys=True))
'''


def _run_index_probe(source: Path, control: RunControl) -> dict[str, Any]:
    repository_root = Path(__file__).resolve().parents[1]
    process = subprocess.Popen(
        [sys.executable, "-c", _INDEX_PROBE, str(source), str(repository_root)],
        cwd=repository_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        while True:
            control.check()
            try:
                stdout, stderr = process.communicate(timeout=min(0.25, max(0.01, control.remaining())))
                break
            except subprocess.TimeoutExpired:
                continue
    except BaseException:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        raise

    try:
        observed = json.loads(stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        return {
            "status": "FAILED",
            "return_code": process.returncode,
            "error": f"Index probe did not return JSON: {exc}",
            "stderr_tail": (stderr or "")[-2000:],
        }
    if process.returncode != 0 or not observed.get("ok"):
        return {
            "status": "FAILED",
            "return_code": process.returncode,
            "error_type": observed.get("error_type", "IndexProbeProcessError"),
            "error": observed.get("error", "index probe failed"),
            "stderr_tail": (stderr or "")[-2000:],
        }
    expected = observed["actual_index_selection"]
    # The source-side prediction is populated by the streaming inventory. The
    # caller fills concordance after this function returns.
    return {"status": "MEASURED", **observed}


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _write_initial_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def run_inventory(
    source: str | Path,
    output_dir: str | Path,
    *,
    expected_sha256: str = PINNED_SOURCE_SHA256,
    expected_size_bytes: int | None = PINNED_SOURCE_SIZE,
    deadline_seconds: float = DEFAULT_DEADLINE_SECONDS,
    checkpoint_seconds: float = DEFAULT_CHECKPOINT_SECONDS,
    measure_existing_index: bool = False,
    cancel_event: Any = None,
    _monotonic: Callable[[], float] | None = None,
) -> dict[str, Any]:
    """Write a complete inventory or an explicit incomplete-prefix record."""
    if deadline_seconds < 0:
        raise ValueError("deadline_seconds must be nonnegative")
    if checkpoint_seconds < 0:
        raise ValueError("checkpoint_seconds must be nonnegative")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("expected_sha256 must be 64 hexadecimal characters")

    source_path = Path(source).resolve()
    output_path = Path(output_dir).absolute()
    output_path.mkdir(exist_ok=False)
    manifest_path = output_path / "manifest.json"
    inventory_path = output_path / "inventory.json"
    control = RunControl(deadline_seconds, cancel_event, _monotonic)
    state = InventoryState()
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "run_status": "RUNNING",
        "started_utc": _utc_now(),
        "source": {
            "path": str(source_path),
            "expected_size_bytes": expected_size_bytes,
            "expected_sha256": expected_sha256.lower(),
            "initial_stat_before_hash": None,
            "initial_stat_after_hash": None,
            "initial_sha256": None,
            "initial_sha256_verified": False,
            "scan_stat_before": None,
            "scan_stat_after": None,
            "final_stat_before_hash": None,
            "final_stat_after_hash": None,
            "final_sha256": None,
            "final_sha256_verified": False,
            "stable_file_check": "NOT_COMPLETED",
        },
        "execution": {
            "pid": os.getpid(),
            "deadline_seconds": deadline_seconds,
            "checkpoint_seconds": checkpoint_seconds,
            "existing_index_measurement_requested": measure_existing_index,
            "existing_index_measurement": {"status": "NOT_REQUESTED"},
        },
        "stop_reason": None,
    }
    _write_initial_json(manifest_path, manifest)
    _write_initial_json(
        inventory_path,
        state.observed_payload("RUNNING", "NOT_FINALIZED"),
    )

    stop_reason: str | None = None
    source_stat_records: list[dict[str, int]] = []
    initial_digest: str | None = None
    final_digest: str | None = None
    source_identity_initial_ok = False
    source_identity_final_ok = False
    scan_exception: Exception | None = None
    hard_stop = False
    scan_start_monotonic: float | None = None
    scan_elapsed_seconds: float | None = None
    measurement: dict[str, Any] = {"status": "NOT_REQUESTED"}
    derived_summary: dict[str, Any] | None = None
    derived_summary_status = "NOT_FINALIZED"
    last_checkpoint = control._monotonic()

    def save_manifest() -> None:
        _atomic_json(manifest_path, manifest)

    def checkpoint() -> None:
        nonlocal last_checkpoint
        _atomic_json(
            inventory_path,
            state.observed_payload(stop_reason or "RUNNING", derived_summary_status),
        )
        last_checkpoint = control._monotonic()

    try:
        control.check()
        manifest["source"]["initial_stat_before_hash"] = _stat_record(source_path)
        source_stat_records.append(manifest["source"]["initial_stat_before_hash"])
        initial_digest = _hash_file(source_path, control)
        manifest["source"]["initial_sha256"] = initial_digest
        manifest["source"]["initial_stat_after_hash"] = _stat_record(source_path)
        source_stat_records.append(manifest["source"]["initial_stat_after_hash"])
        size_ok = (
            expected_size_bytes is None
            or manifest["source"]["initial_stat_after_hash"]["size_bytes"] == expected_size_bytes
        )
        source_identity_initial_ok = (
            initial_digest == expected_sha256.lower()
            and size_ok
            and _same_stat(*source_stat_records)
        )
        manifest["source"]["initial_sha256_verified"] = (
            initial_digest == expected_sha256.lower() and size_ok
        )
        if not source_identity_initial_ok:
            detail = []
            if initial_digest != expected_sha256.lower():
                detail.append("SHA256 differs from expected source")
            if not size_ok:
                detail.append("source byte size differs from expected size")
            if not _same_stat(*source_stat_records):
                detail.append("source changed during initial hash")
            raise SourceIdentityError("; ".join(detail))

        manifest["source"]["scan_stat_before"] = _stat_record(source_path)
        source_stat_records.append(manifest["source"]["scan_stat_before"])
        scan_start_monotonic = control._monotonic()
        with _open_gtf(source_path) as stream:
            for line_number, line in enumerate(stream, 1):
                control.check()
                state.consume(line, line_number)
                now = control._monotonic()
                if checkpoint_seconds and now - last_checkpoint >= checkpoint_seconds:
                    checkpoint()
        state.eof_reached = True
        if scan_start_monotonic is not None:
            scan_elapsed_seconds = max(0.0, control._monotonic() - scan_start_monotonic)
        manifest["source"]["scan_stat_after"] = _stat_record(source_path)
        source_stat_records.append(manifest["source"]["scan_stat_after"])

        control.check()
        derived_summary = state.summary(control)
        derived_summary_status = "FINALIZED"

        if measure_existing_index:
            state.release_metadata_for_index_probe()
            measurement = {"status": "RUNNING"}
            manifest["execution"]["existing_index_measurement"] = measurement
            save_manifest()
            control.check()
            measurement = _run_index_probe(source_path, control)
            if measurement.get("status") == "MEASURED":
                expected_fingerprint = state.index_fingerprint.to_json()
                actual_fingerprint = measurement["actual_index_selection"]
                measurement["source_selection_prediction"] = expected_fingerprint
                measurement["selection_fingerprint_concordant"] = (
                    expected_fingerprint == actual_fingerprint
                )
                measurement["selection_comparison"] = (
                    "concordant" if measurement["selection_fingerprint_concordant"] else "DISCORDANT"
                )
            manifest["execution"]["existing_index_measurement"] = measurement

        control.check()
        manifest["source"]["final_stat_before_hash"] = _stat_record(source_path)
        final_stat_before = manifest["source"]["final_stat_before_hash"]
        final_digest = _hash_file(source_path, control)
        manifest["source"]["final_sha256"] = final_digest
        manifest["source"]["final_stat_after_hash"] = _stat_record(source_path)
        source_stat_records.extend((final_stat_before, manifest["source"]["final_stat_after_hash"]))
        source_identity_final_ok = (
            final_digest == expected_sha256.lower()
            and final_digest == initial_digest
            and _same_stat(*source_stat_records)
        )
        manifest["source"]["final_sha256_verified"] = (
            final_digest == expected_sha256.lower() and final_digest == initial_digest
        )
        manifest["source"]["stable_file_check"] = (
            "PASS" if source_identity_initial_ok and source_identity_final_ok else "FAIL"
        )
        if not source_identity_final_ok:
            raise SourceIdentityError("source SHA256 or file identity changed during inventory")
    except (DeadlineExpired, RunCancelled) as exc:
        stop_reason = f"{type(exc).__name__}: {exc}"
        hard_stop = True
        if measurement.get("status") == "RUNNING":
            measurement = {"status": "INTERRUPTED", "reason": stop_reason}
    except Exception as exc:
        scan_exception = exc
        stop_reason = f"{type(exc).__name__}: {exc}"
        if measurement.get("status") == "RUNNING":
            measurement = {"status": "FAILED", "reason": stop_reason}

    # On an ordinary parser/read failure, try the final source hash while the
    # run still has time. Deadline and cancellation stops preserve the prefix
    # immediately and mark the final hash as not attempted.
    if initial_digest is not None and not hard_stop and manifest["source"]["final_sha256"] is None:
        try:
            control.check()
            manifest["source"]["final_stat_before_hash"] = _stat_record(source_path)
            final_stat_before = manifest["source"]["final_stat_before_hash"]
            final_digest = _hash_file(source_path, control)
            manifest["source"]["final_sha256"] = final_digest
            manifest["source"]["final_stat_after_hash"] = _stat_record(source_path)
            source_stat_records.extend((final_stat_before, manifest["source"]["final_stat_after_hash"]))
            source_identity_final_ok = (
                final_digest == expected_sha256.lower()
                and final_digest == initial_digest
                and _same_stat(*source_stat_records)
            )
            manifest["source"]["final_sha256_verified"] = (
                final_digest == expected_sha256.lower() and final_digest == initial_digest
            )
            manifest["source"]["stable_file_check"] = (
                "PASS" if source_identity_initial_ok and source_identity_final_ok else "FAIL"
            )
            if not source_identity_final_ok:
                stop_reason = "SourceIdentityError: source SHA256 or file identity changed during inventory"
        except (DeadlineExpired, RunCancelled) as exc:
            stop_reason = f"{type(exc).__name__}: {exc}"
            hard_stop = True
        except Exception as exc:
            stop_reason = f"{type(exc).__name__}: final source verification failed: {exc}"

    if derived_summary is None and state.eof_reached and not hard_stop:
        try:
            control.check()
            derived_summary = state.summary(control)
            derived_summary_status = "FINALIZED"
        except (DeadlineExpired, RunCancelled) as exc:
            stop_reason = f"{type(exc).__name__}: {exc}"
            hard_stop = True
        except Exception as exc:
            stop_reason = f"{type(exc).__name__}: summary failed: {exc}"

    run_complete = (
        state.eof_reached
        and source_identity_initial_ok
        and source_identity_final_ok
        and manifest["source"]["stable_file_check"] == "PASS"
        and derived_summary is not None
        and not hard_stop
        and stop_reason is None
    )
    if run_complete:
        inventory = derived_summary
        inventory["scope"]["status"] = "COMPLETE"
        inventory["scope"]["counts_scope"] = "FULL_SOURCE_EOF"
        inventory["scope"]["counts_complete"] = True
        inventory["scope"]["eof_reached"] = True
        inventory["scope"]["source_sha256_verified"] = True
        inventory["scope"]["stable_file_check"] = "PASS"
        manifest["run_status"] = "COMPLETE"
        stop_reason = None
    else:
        if stop_reason is None:
            if not state.eof_reached:
                stop_reason = "scan did not reach full EOF"
            elif not source_identity_initial_ok or not source_identity_final_ok:
                stop_reason = "source identity or stable-file check did not pass"
            else:
                stop_reason = "complete inventory could not be finalized"
        inventory = state.observed_payload(stop_reason, derived_summary_status)
        inventory["scope"]["eof_reached"] = state.eof_reached
        inventory["scope"]["counts_scope"] = (
            "FULL_SOURCE_EOF" if state.eof_reached else "OBSERVED_PREFIX"
        )
        inventory["scope"]["counts_complete"] = state.eof_reached
        inventory["scope"]["source_sha256_verified"] = bool(
            source_identity_initial_ok and source_identity_final_ok
        )
        inventory["scope"]["stable_file_check"] = manifest["source"]["stable_file_check"]
        if derived_summary is not None:
            inventory["available_full_EOF_summary"] = derived_summary
        manifest["run_status"] = "INCOMPLETE"

    manifest["finished_utc"] = _utc_now()
    manifest["stop_reason"] = stop_reason
    manifest["execution"]["existing_index_measurement"] = measurement
    manifest["execution"]["scan_eof_reached"] = state.eof_reached
    manifest["execution"]["last_line_number"] = state.last_line_number
    if scan_elapsed_seconds is not None:
        manifest["execution"]["scan_elapsed_seconds"] = scan_elapsed_seconds
    manifest["execution"]["observed_error_type"] = (
        type(scan_exception).__name__ if scan_exception is not None else None
    )
    manifest["execution"]["observed_error"] = str(scan_exception) if scan_exception is not None else None

    # Final inventory first, then final manifest. A process stopped during a
    # scan still leaves the most recent inventory checkpoint and this status.
    _atomic_json(inventory_path, inventory)
    save_manifest()
    return {
        "run_status": manifest["run_status"],
        "stop_reason": stop_reason,
        "output_dir": str(output_path),
        "inventory_path": str(inventory_path),
        "manifest_path": str(manifest_path),
        "eof_reached": state.eof_reached,
        "counts_complete": state.eof_reached,
    }


def _install_signal_handlers(cancel_event: Any) -> dict[int, Any]:
    previous: dict[int, Any] = {}

    def request_cancel(_signum: int, _frame: Any) -> None:
        cancel_event.set()

    for signum in (signal.SIGINT, signal.SIGTERM):
        previous[signum] = signal.getsignal(signum)
        signal.signal(signum, request_cancel)
    return previous


def _restore_signal_handlers(previous: dict[int, Any]) -> None:
    for signum, handler in previous.items():
        signal.signal(signum, handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="whole GTF or GTF.GZ")
    parser.add_argument("--output-dir", type=Path, required=True, help="new, exclusive output leaf")
    parser.add_argument("--expected-sha256", default=PINNED_SOURCE_SHA256)
    parser.add_argument("--expected-size-bytes", type=int, default=PINNED_SOURCE_SIZE)
    parser.add_argument("--deadline-seconds", type=float, default=DEFAULT_DEADLINE_SECONDS)
    parser.add_argument("--checkpoint-seconds", type=float, default=DEFAULT_CHECKPOINT_SECONDS)
    parser.add_argument(
        "--measure-existing-index",
        action="store_true",
        help="measure the current cohort _read_gtf in an isolated child process",
    )
    args = parser.parse_args(argv)

    import threading

    cancel_event = threading.Event()
    previous = _install_signal_handlers(cancel_event)
    try:
        result = run_inventory(
            args.source,
            args.output_dir,
            expected_sha256=args.expected_sha256,
            expected_size_bytes=args.expected_size_bytes,
            deadline_seconds=args.deadline_seconds,
            checkpoint_seconds=args.checkpoint_seconds,
            measure_existing_index=args.measure_existing_index,
            cancel_event=cancel_event,
        )
    finally:
        _restore_signal_handlers(previous)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["run_status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
