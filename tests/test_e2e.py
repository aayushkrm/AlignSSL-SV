"""End-to-end pipeline smoke test on synthetic data.

Proves the full Stage-1 machinery runs and *learns* before touching real
1000G BAMs: synth genome+BAM -> tensorize -> SSL (MAE+VICReg) step ->
fine-tune deletion head -> temperature scaling + conformal + ECE.

Run:  python -m tests.test_e2e   (from alignssl_sv/)
"""
import os, sys, tempfile
import numpy as np
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from alignssl.synth import make_reference, simulate_bam
from alignssl.data import PretrainDataset, FinetuneDataset
from alignssl.encoder import AlignEncoder
from alignssl.ssl import (MAEDecoder, Projector, column_targets, mae_mask,
                          mae_loss, vicreg_loss, subsample_rows)
from alignssl.heads import (SVHeads, finetune_loss, TemperatureScaler,
                            mc_dropout_predict, expected_calibration_error,
                            ConformalBinary)
from alignssl.tensorize import N_CHANNELS

torch.manual_seed(0); np.random.seed(0)
CHROM = "chr21"; W = 256


def build_fixture(tmp):
    fa = os.path.join(tmp, "ref.fa"); bam = os.path.join(tmp, "s.bam")
    seq = make_reference(fa, chrom=CHROM, length=24_000, seed=1)
    # implant deletions of varied size (length-stratified: 300bp, 1.5kb, 4kb)
    truth = [(8_000, 8_300), (12_000, 12_800), (18_000, 20_000)]
    simulate_bam(bam, seq, chrom=CHROM, deletions=truth,
                 coverage=30, seed=2)
    return fa, bam, truth


def main():
    tmp = tempfile.mkdtemp()
    fa, bam, truth = build_fixture(tmp)
    print(f"[fixture] ref+BAM built, {len(truth)} deletions:", truth)

    # ---------- Stage 1a: SSL pretraining step ----------
    pre = PretrainDataset(bam, fa, CHROM, win_width=W, stride=256,
                          max_rows=64, limit=24)
    dl = DataLoader(pre, batch_size=8, shuffle=True)
    enc = AlignEncoder(in_ch=N_CHANNELS, d_model=128)
    dec = MAEDecoder(128)
    proj = Projector(128)
    params = list(enc.parameters()) + list(dec.parameters()) + list(proj.parameters())
    opt = torch.optim.AdamW(params, lr=1e-3)
    g = torch.Generator().manual_seed(0)

    enc.train()
    losses = []
    for epoch in range(3):
        for x in dl:
            opt.zero_grad()
            # MAE branch
            xm, colmask = mae_mask(x, 0.4, generator=g)
            _, cols = enc(xm, return_cols=True)
            pred = dec(cols)
            tgt = column_targets(x)
            l_mae = mae_loss(pred, tgt, colmask)
            # VICReg branch: two coverage views
            v1 = subsample_rows(x, 0.7, generator=g)
            v2 = subsample_rows(x, 0.5, generator=g)
            z1 = proj(enc(v1)); z2 = proj(enc(v2))
            l_vic, _ = vicreg_loss(z1, z2)
            loss = l_mae + 0.5 * l_vic
            loss.backward(); opt.step()
            losses.append(loss.item())
    print(f"[SSL] pretrain loss {losses[0]:.3f} -> {losses[-1]:.3f} "
          f"(dropped {'YES' if losses[-1] < losses[0] else 'NO'})")

    # ---------- Stage 1b: fine-tune deletion head ----------
    ft = FinetuneDataset(bam, fa, CHROM, truth, win_width=W, max_rows=64,
                         n_neg_per_pos=4, seed=3)
    n = len(ft); idx = np.arange(n); np.random.shuffle(idx)
    cut = int(0.6 * n); cut2 = int(0.8 * n)
    tr, ca, te = idx[:cut], idx[cut:cut2], idx[cut2:]
    def loader(ix): return DataLoader(torch.utils.data.Subset(ft, ix.tolist()),
                                      batch_size=8, shuffle=True)
    heads = SVHeads(128)
    opt2 = torch.optim.AdamW(list(enc.parameters()) + list(heads.parameters()), lr=1e-3)
    enc.train(); heads.train()
    for epoch in range(10):
        for b in loader(tr):
            opt2.zero_grad()
            z = enc(b["x"]); out = heads(z)
            loss, logs = finetune_loss(out, b, a=1.0, b=1.0)
            loss.backward(); opt2.step()
    print(f"[FT] final train loss {logs['total']:.3f}")

    # ---------- eval + calibration ----------
    enc.eval(); heads.eval()
    def collect(ix):
        L, Y = [], []
        with torch.no_grad():
            for b in loader(ix):
                z = enc(b["x"]); L.append(heads(z)["cls_logits"]); Y.append(b["label"])
        return torch.cat(L), torch.cat(Y)
    logit_ca, y_ca = collect(ca)
    logit_te, y_te = collect(te)
    from torch.nn.functional import softmax
    pred = logit_te.argmax(-1)
    acc = (pred == y_te).float().mean().item()
    # temperature scaling on calib split
    ts = TemperatureScaler(); T = ts.fit(logit_ca, y_ca)
    ece_before = expected_calibration_error(softmax(logit_te, -1), y_te)
    ece_after = expected_calibration_error(softmax(ts(logit_te), -1), y_te)
    # conformal
    conf = ConformalBinary(alpha=0.2)
    conf.calibrate(softmax(logit_ca, -1)[:, 1].numpy(), y_ca.numpy())
    sets = conf.predict_set(softmax(logit_te, -1)[:, 1].numpy())
    covered = sets[np.arange(len(y_te)), y_te.numpy()].mean()
    print(f"[EVAL] test acc={acc:.3f} | T={T:.3f} | "
          f"ECE {ece_before:.3f}->{ece_after:.3f} | conformal cov={covered:.3f} (target 0.8)")
    # MC-dropout uncertainty sanity
    b0 = next(iter(loader(te)))
    unc = mc_dropout_predict(lambda x: heads(enc(x))["cls_logits"], b0["x"], n_samples=10)
    print(f"[UNC] mean epistemic={unc['epistemic'].mean():.4f} "
          f"aleatoric={unc['aleatoric'].mean():.4f}")

    ok = (losses[-1] < losses[0]) and (acc >= 0.7)
    print("\nSMOKE TEST:", "PASS" if ok else "CHECK")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
