"""Write a frozen, entirely synthetic positive LiftOn interface fixture."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import tempfile

VERSION = "lifton-interface-v1"
SEED = 20261010
CODONS = dict(zip("ACDEFGHIKLMNPQRSTVWY", "GCT TGT GAT GAA TTT GGT CAT ATT AAA CTT ATG AAT CCT CAA CGT TCT ACT GTT TGG TAT".split()))
COMPLEMENT = str.maketrans("ACGT", "TGCA")


def reverse_complement(sequence):
    return sequence.translate(COMPLEMENT)[::-1]


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def fixture_payloads():
    rng = random.Random(SEED)
    background = lambda n: "".join(rng.choice("ACGT") for _ in range(n))
    peptide = lambda n: "".join(rng.choice(tuple(CODONS)) for _ in range(n))
    dna = lambda protein: "".join(CODONS[aa] for aa in protein)
    refs = {name: list(background(4000)) for name in ("ref_plus", "ref_minus")}
    targets = {name: list(background(4000)) for name in ("target_plus", "target_minus", "target_extra")}
    # Shared terminal exons; two distinct internal exons for the plus gene.
    plus = [dna("M" + peptide(49)), dna(peptide(50)), dna(peptide(50)), dna(peptide(50)) + "TAA"]
    minus = [dna("M" + peptide(49)), dna(peptide(50)), dna(peptide(50)) + "TAA"]
    genes = [
        ("SYNTHG0001.1", "ref_plus", "+", 400,
         [("SYNTHT0001.1", [(300, plus[0]), (700, plus[1]), (1100, plus[3])]),
          ("SYNTHT0002.1", [(300, plus[0]), (900, plus[2]), (1100, plus[3])])],
         [("C0", "target_plus", 1200), ("C1", "target_extra", 1800)]),
        ("SYNTHG0002.1", "ref_minus", "-", 800,
         [("SYNTHT0003.1", [(1100, minus[0]), (700, minus[1]), (300, minus[2])])],
         [("C0", "target_minus", 600)]),
    ]
    gffs = {"reference.gff3": ["##gff-version 3"], "expected_target.gff3": ["##gff-version 3"]}
    for filename, sequences in zip(gffs, (refs, targets)):
        gffs[filename] += [f"##sequence-region {name} 1 {len(seq)}" for name, seq in sequences.items()]
    truth = {"fixture_version": VERSION, "seed": SEED,
             "coordinates": "1-based closed; CDS blocks and codon positions in transcript order",
             "terminal_stop_in_CDS": True, "native_IDs": "UNKNOWN until native run", "transcripts": []}
    crosswalk = ["ref_gene_id\tref_transcript_id\tfixture_copy_id\texpected_target_gene_id\texpected_target_transcript_id\ttarget_seqid\ttarget_strand"]

    def row(seqid, kind, start, end, strand, phase, attrs):
        return "\t".join(map(str, (seqid, "synthetic", kind, start, end, ".", strand, phase, attrs)))

    def model(seqid, strand, offset, chain):
        blocks = [{"start": offset + pos + 1, "end": offset + pos + len(seq), "phase": 0} for pos, seq in chain]
        positions = [(range(b["start"], b["end"] + 1) if strand == "+" else
                      range(b["end"], b["start"] - 1, -1)) for b in blocks]
        first, last = list(positions[0]), list(positions[-1])
        return {"seqid": seqid, "strand": strand, "CDS_blocks": blocks,
                "start_codon_positions": first[:3], "stop_codon_positions": last[-3:]}

    def annotation(filename, seqid, strand, offset, gene_id, transcripts):
        bounds = [(offset + p + 1, offset + p + len(s)) for _, chain in transcripts for p, s in chain]
        lo, hi = min(a for a, _ in bounds), max(b for _, b in bounds)
        gffs[filename].append(row(seqid, "gene", lo, hi, strand, ".", f"ID={gene_id};gene_id={gene_id};gene_biotype=protein_coding;gene_type=protein_coding"))
        for tx_id, chain in transcripts:
            blocks = model(seqid, strand, offset, chain)["CDS_blocks"]
            lo, hi = min(b["start"] for b in blocks), max(b["end"] for b in blocks)
            attrs = f"ID={tx_id};Parent={gene_id};gene_id={gene_id};transcript_id={tx_id};transcript_biotype=protein_coding;transcript_type=protein_coding"
            gffs[filename].append(row(seqid, "mRNA", lo, hi, strand, ".", attrs))
            for i, block in enumerate(blocks, 1):
                for kind, phase in (("exon", "."), ("CDS", 0)):
                    attrs = f"ID={tx_id}.{kind}{i};Parent={tx_id}"
                    gffs[filename].append(row(seqid, kind, block["start"], block["end"], strand, phase, attrs))

    for gene_id, ref_seqid, strand, ref_offset, transcripts, copies in genes:
        island = list(background(1800))
        for _, chain in transcripts:
            for pos, sequence in chain:
                island[pos:pos + len(sequence)] = sequence if strand == "+" else reverse_complement(sequence)
            for (pos, sequence), (next_pos, next_sequence) in zip(chain, chain[1:]):
                if strand == "+":
                    island[pos + len(sequence):pos + len(sequence) + 2] = "GT"
                    island[next_pos - 2:next_pos] = "AG"
                else:
                    island[pos - 2:pos] = "AC"
                    island[next_pos + len(next_sequence):next_pos + len(next_sequence) + 2] = "CT"
        refs[ref_seqid][ref_offset:ref_offset + len(island)] = island
        annotation("reference.gff3", ref_seqid, strand, ref_offset, gene_id, transcripts)
        for copy_id, seqid, offset in copies:
            targets[seqid][offset:offset + len(island)] = island
            annotation("expected_target.gff3", seqid, strand, offset, f"FIXTURE.{gene_id}.{copy_id}",
                       [(f"FIXTURE.{tx_id}.{copy_id}", chain) for tx_id, chain in transcripts])
        for tx_id, chain in transcripts:
            coding = "".join(seq for _, seq in chain)
            inverse = {codon: aa for aa, codon in CODONS.items()}
            protein = "".join(inverse[coding[i:i + 3]] for i in range(0, len(coding) - 3, 3))
            reference = model(ref_seqid, strand, ref_offset, chain)
            entry = {"ref_gene_id": gene_id, "ref_transcript_id": tx_id, "reference": reference,
                     "coding_DNA": coding, "coding_DNA_sha256": _sha(coding.encode()),
                     "protein": protein, "protein_sha256": _sha(protein.encode()), "targets": []}
            for copy_id, seqid, offset in copies:
                target = model(seqid, strand, offset, chain)
                target.update(fixture_copy_id=copy_id, expected_gene_id=f"FIXTURE.{gene_id}.{copy_id}",
                              expected_transcript_id=f"FIXTURE.{tx_id}.{copy_id}",
                              reference_to_target_CDS_blocks=list(zip(reference["CDS_blocks"], target["CDS_blocks"])))
                entry["targets"].append(target)
                crosswalk.append("\t".join((gene_id, tx_id, copy_id, target["expected_gene_id"], target["expected_transcript_id"], seqid, strand)))
            truth["transcripts"].append(entry)
    payloads = {}
    for filename, sequences in (("reference.fa", refs), ("target.fa", targets)):
        payloads[filename] = "".join(f">{name}\n" + "\n".join("".join(seq[i:i + 80]) for i in range(0, len(seq), 80)) + "\n" for name, seq in sequences.items()).encode()
    payloads.update({name: ("\n".join(lines) + "\n").encode() for name, lines in gffs.items()})
    payloads["truth.json"] = _json(truth)
    payloads["expected_crosswalk.tsv"] = ("\n".join(crosswalk) + "\n").encode()
    payloads["manifest.json"] = _json({"fixture_version": VERSION, "seed": SEED,
        "files": {name: {"bytes": len(data), "sha256": _sha(data)} for name, data in sorted(payloads.items())}})
    return payloads


def create_fixture(output_dir):
    raw = Path(output_dir).absolute()
    if raw.is_symlink():
        raise FileExistsError(f"Refusing symlink output: {raw}")
    if any(parent.is_symlink() for parent in raw.parents):
        raise ValueError("Output ancestors must not be symlinks")
    root = raw.parent.resolve(strict=True) / raw.name
    payloads = fixture_payloads()
    root.mkdir()  # Exclusive claim; never reuse even an empty output directory.
    with tempfile.TemporaryDirectory(prefix=".staging-", dir=root) as staged:
        for name, data in payloads.items():  # Manifest is published last.
            temporary = Path(staged) / name
            with temporary.open("xb") as handle:
                handle.write(data)
            os.replace(temporary, root / name)
    return root


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    print(f"Created {VERSION}: {create_fixture(args.output_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
