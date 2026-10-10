import hashlib
import itertools
import json
from pathlib import Path

import pytest

from analysis.make_lifton_interface_fixture import SEED, VERSION, create_fixture, main


def fasta(path):
    sequences = {}
    for line in path.read_text().splitlines():
        if line.startswith(">"):
            name = line[1:]
            assert name not in sequences
            sequences[name] = ""
        else:
            sequences[name] += line
    return sequences


def gff(path):
    features = {}
    for line in path.read_text().splitlines():
        if line.startswith("#"):
            continue
        fields = line.split("\t")
        assert len(fields) == 9
        attrs = dict(item.split("=", 1) for item in fields[8].split(";"))
        assert attrs["ID"] not in features
        features[attrs["ID"]] = dict(seqid=fields[0], kind=fields[2], start=int(fields[3]),
                                     end=int(fields[4]), strand=fields[6], phase=fields[7], attrs=attrs)
    return features


def extract(sequences, model):
    pieces = []
    for block in model["CDS_blocks"]:
        piece = sequences[model["seqid"]][block["start"] - 1:block["end"]]
        if model["strand"] == "-":
            piece = piece.translate(str.maketrans("ACGT", "TGCA"))[::-1]
        pieces.append(piece)
    return "".join(pieces)


def codon_at(sequences, model, key):
    codon = "".join(sequences[model["seqid"]][pos - 1] for pos in model[key])
    return codon if model["strand"] == "+" else codon.translate(str.maketrans("ACGT", "TGCA"))


def translate(dna):
    # Independent full standard genetic code; generator uses a restricted set.
    bases = "TCAG"
    amino = "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"
    code = dict(zip(map("".join, itertools.product(bases, repeat=3)), amino))
    return "".join(code[dna[i:i + 3]] for i in range(0, len(dna), 3))


@pytest.fixture
def fixture(tmp_path):
    return create_fixture(tmp_path / "fixture")


def test_deterministic_bytes_hash_manifest_and_size(fixture, tmp_path):
    second = create_fixture(tmp_path / "second")
    names = {p.name for p in fixture.iterdir()}
    assert names == {"reference.fa", "target.fa", "reference.gff3", "expected_target.gff3",
                     "expected_crosswalk.tsv", "truth.json", "manifest.json"}
    assert all((fixture / name).read_bytes() == (second / name).read_bytes() for name in names)
    manifest = json.loads((fixture / "manifest.json").read_text())
    # Immutable v1 content; future intentional changes require a version decision.
    assert hashlib.sha256((fixture / "manifest.json").read_bytes()).hexdigest() == "684b56f9b566e4eb3d100fdd0f07785a7acc09c9bfb354d60a9d1ff70a7c4867"
    assert manifest["fixture_version"] == VERSION == "lifton-interface-v1"
    assert manifest["seed"] == SEED == 20261010
    assert set(manifest["files"]) == names - {"manifest.json"}
    for name, metadata in manifest["files"].items():
        data = (fixture / name).read_bytes()
        assert metadata == {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    reference, target = fasta(fixture / "reference.fa"), fasta(fixture / "target.fa")
    assert set(reference) == {"ref_plus", "ref_minus"}
    assert set(target) == {"target_plus", "target_minus", "target_extra"}
    assert sum(map(len, reference.values())) == 8000
    assert sum(map(len, target.values())) == 12000
    assert sum((fixture / name).stat().st_size for name in ("reference.fa", "target.fa")) <= 30000
    assert all(set(seq) == set("ACGT") for seq in (*reference.values(), *target.values()))
    # Noncoding backgrounds are independently generated; only constructed loci match.
    assert len({seq[:300] for seq in (*reference.values(), *target.values())}) == 5
    assert reference["ref_plus"][400:2200] == target["target_plus"][1200:3000]
    assert reference["ref_plus"][400:2200] == target["target_extra"][1800:3600]
    assert reference["ref_minus"][800:2600] == target["target_minus"][600:2400]


def test_all_isoforms_copies_orientation_frame_and_explicit_termini(fixture):
    truth = json.loads((fixture / "truth.json").read_text())
    refs, targets = fasta(fixture / "reference.fa"), fasta(fixture / "target.fa")
    assert truth["native_IDs"] == "UNKNOWN until native run"
    entries = truth["transcripts"]
    assert {e["ref_gene_id"] for e in entries} == {"SYNTHG0001.1", "SYNTHG0002.1"}
    assert {e["ref_transcript_id"] for e in entries} == {"SYNTHT0001.1", "SYNTHT0002.1", "SYNTHT0003.1"}
    assert len({e["protein"] for e in entries}) == 3
    assert {e["reference"]["strand"] for e in entries} == {"+", "-"}
    assert sum(len(e["targets"]) for e in entries) == 5
    expected_rows = set()
    for entry in entries:
        coding = entry["coding_DNA"]
        assert len(coding) == 453 and coding[:3] == "ATG" and coding[-3:] == "TAA"
        assert translate(coding) == entry["protein"] + "*"
        assert len(entry["protein"]) == 150 and "*" not in entry["protein"]
        assert entry["coding_DNA_sha256"] == hashlib.sha256(coding.encode()).hexdigest()
        assert entry["protein_sha256"] == hashlib.sha256(entry["protein"].encode()).hexdigest()
        models = [(refs, entry["reference"])] + [(targets, t) for t in entry["targets"]]
        for sequences, model in models:
            assert extract(sequences, model) == coding
            assert codon_at(sequences, model, "start_codon_positions") == "ATG"
            assert codon_at(sequences, model, "stop_codon_positions") == "TAA"
            blocks = model["CDS_blocks"]
            assert len(blocks) == 3
            assert all(b["phase"] == 0 and (b["end"] - b["start"] + 1) % 3 == 0 for b in blocks)
            assert [b["start"] for b in blocks] == sorted((b["start"] for b in blocks), reverse=model["strand"] == "-")
            for left, right in zip(blocks, blocks[1:]):
                seq = sequences[model["seqid"]]
                if model["strand"] == "+":
                    assert seq[left["end"]:left["end"] + 2] == "GT"
                    assert seq[right["start"] - 3:right["start"] - 1] == "AG"
                else:
                    assert seq[left["start"] - 3:left["start"] - 1] == "AC"
                    assert seq[right["end"]:right["end"] + 2] == "CT"
        for target in entry["targets"]:
            assert target["reference_to_target_CDS_blocks"] == list(map(list, zip(entry["reference"]["CDS_blocks"], target["CDS_blocks"])))
            shift = target["CDS_blocks"][0]["start"] - entry["reference"]["CDS_blocks"][0]["start"]
            for key in ("start_codon_positions", "stop_codon_positions"):
                assert target[key] == [pos + shift for pos in entry["reference"][key]]
            expected_rows.add("\t".join((entry["ref_gene_id"], entry["ref_transcript_id"], target["fixture_copy_id"], target["expected_gene_id"], target["expected_transcript_id"], target["seqid"], target["strand"])))
        assert {t["fixture_copy_id"] for t in entry["targets"]} == ({"C0", "C1"} if entry["ref_gene_id"] == "SYNTHG0001.1" else {"C0"})
    assert set((fixture / "expected_crosswalk.tsv").read_text().splitlines()[1:]) == expected_rows


@pytest.mark.parametrize("gff_name,fa_name,genes,transcripts", [
    ("reference.gff3", "reference.fa", 2, 3), ("expected_target.gff3", "target.fa", 3, 5)])
def test_gff3_hierarchy_biotypes_and_truth_chains(fixture, gff_name, fa_name, genes, transcripts):
    features, sequences = gff(fixture / gff_name), fasta(fixture / fa_name)
    assert sum(f["kind"] == "gene" for f in features.values()) == genes
    assert sum(f["kind"] == "mRNA" for f in features.values()) == transcripts
    assert sum(f["kind"] == "CDS" for f in features.values()) == transcripts * 3
    for feature in features.values():
        assert 1 <= feature["start"] <= feature["end"] <= len(sequences[feature["seqid"]])
        if feature["kind"] == "gene":
            assert feature["attrs"]["gene_biotype"] == feature["attrs"]["gene_type"] == "protein_coding"
        else:
            parent = features[feature["attrs"]["Parent"]]
            assert parent["start"] <= feature["start"] <= feature["end"] <= parent["end"]
            assert (parent["seqid"], parent["strand"]) == (feature["seqid"], feature["strand"])
            if feature["kind"] == "mRNA":
                assert parent["kind"] == "gene" and feature["attrs"]["transcript_biotype"] == "protein_coding"
            else:
                assert parent["kind"] == "mRNA"
    truth = json.loads((fixture / "truth.json").read_text())
    for entry in truth["transcripts"]:
        pairs = [(entry["ref_transcript_id"], entry["reference"])] if gff_name == "reference.gff3" else [(t["expected_transcript_id"], t) for t in entry["targets"]]
        for tx_id, model in pairs:
            cds = [f for f in features.values() if f["kind"] == "CDS" and f["attrs"].get("Parent") == tx_id]
            assert [(f["start"], f["end"], f["phase"]) for f in cds] == [(b["start"], b["end"], "0") for b in model["CDS_blocks"]]
            assert extract(sequences, model) == entry["coding_DNA"]


@pytest.mark.parametrize("kind", ["directory", "empty_directory", "file", "symlink", "dangling_symlink"])
def test_existing_output_refused_without_changes(tmp_path, kind):
    output = tmp_path / "existing"
    if kind in {"directory", "empty_directory"}:
        output.mkdir()
        if kind == "directory":
            (output / "sentinel").write_bytes(b"keep")
    elif kind == "file":
        output.write_bytes(b"keep")
    else:
        destination = tmp_path / "destination"
        if kind == "symlink":
            destination.mkdir()
            (destination / "sentinel").write_bytes(b"keep")
        output.symlink_to(destination, target_is_directory=True)
    with pytest.raises(FileExistsError):
        create_fixture(output)
    if kind == "directory":
        assert {p.name for p in output.iterdir()} == {"sentinel"}
        assert (output / "sentinel").read_bytes() == b"keep"
    elif kind == "empty_directory":
        assert list(output.iterdir()) == []
    elif kind == "file":
        assert output.read_bytes() == b"keep"
    else:
        assert output.is_symlink()
        assert destination.exists() == (kind == "symlink")
        if kind == "symlink":
            assert (destination / "sentinel").read_bytes() == b"keep"


def test_symlink_parent_and_missing_parent_refused(tmp_path):
    parent = tmp_path / "real"
    parent.mkdir()
    link = tmp_path / "linked"
    link.symlink_to(parent, target_is_directory=True)
    with pytest.raises(ValueError, match="ancestors"):
        create_fixture(link / "fixture")
    with pytest.raises(FileNotFoundError):
        create_fixture(tmp_path / "missing" / "fixture")
    assert list(parent.iterdir()) == []


def test_cli_resolves_output_and_manifest_is_published_last(tmp_path, capsys, monkeypatch):
    import analysis.make_lifton_interface_fixture as writer
    published = []
    replace = writer.os.replace

    def observe(source, destination):
        assert Path(source).is_file() and not Path(destination).exists()
        assert Path(destination).is_absolute()
        published.append(Path(destination).name)
        replace(source, destination)

    monkeypatch.setattr(writer.os, "replace", observe)
    monkeypatch.chdir(tmp_path)
    assert main(["--output-dir", "fixture"]) == 0
    assert str(tmp_path / "fixture") in capsys.readouterr().out
    assert published[-1] == "manifest.json" and len(published) == 7
    assert all(p.is_file() for p in (tmp_path / "fixture").iterdir())


def test_failed_publish_has_no_manifest_and_refuses_reuse(tmp_path, monkeypatch):
    import analysis.make_lifton_interface_fixture as writer
    replace = writer.os.replace
    published = []

    def fail(source, destination):
        if not published:
            replace(source, destination)
            published.append(Path(destination))
            return
        raise OSError("synthetic publication failure")

    monkeypatch.setattr(writer.os, "replace", fail)
    output = tmp_path / "fixture"
    with pytest.raises(OSError, match="synthetic publication failure"):
        create_fixture(output)
    assert output.is_dir() and not (output / "manifest.json").exists()
    assert published == [output / "reference.fa"]
    assert {p.name for p in output.iterdir()} == {"reference.fa"}
    with pytest.raises(FileExistsError):
        create_fixture(output)
