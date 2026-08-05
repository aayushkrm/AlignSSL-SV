#!/usr/bin/env python3
"""Stage 1b — statistic-anchored self-supervised pretraining (SAS).

Same data, same encoder, same schedule as ``pretrain_ssl.py``; only the
pretext objective differs.  Instead of reconstructing masked alignment pixels,
the encoder predicts the twelve alignment summary statistics of the *unmasked*
window from two independently occluded views, with an occlusion-consistency
term and VICReg's variance/covariance terms (see ``alignssl.statssl``).

Rationale is in the manuscript (Section 4.2 control, Sections 4.8/6.3 nulls):
generic masked reconstruction optimises a target largely orthogonal to a
benchmark whose signal is low-dimensional, which is why it bought nothing.

The feature normaliser statistics are accumulated over the pretraining stream
and saved INTO the checkpoint, so fine-tuning standardises with exactly the
values pretraining used.  Do not recompute them downstream.
"""
from __future__ import annotations
import argparse, json, time

import torch
from torch.utils.data import DataLoader

from alignssl.data import ShardDataset, MemmapDataset
from alignssl.encoder import AlignEncoder
from alignssl.features import batch_features, FeatureNormalizer
from alignssl.ssl import Projector
from alignssl.statssl import (StatHead, occlude, sas_loss,
                              W_STAT_DEFAULT, W_CONSIST_DEFAULT,
                              W_VICREG_DEFAULT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-dir", required=True)
    ap.add_argument("--memmap", default=None)
    ap.add_argument("--out", required=True, help="encoder checkpoint path")
    ap.add_argument("--split", default="train")
    ap.add_argument("--glob", default="*.npz")
    ap.add_argument("--epochs", type=int, default=25)
    ap.add_argument("--batch-size", type=int, default=96)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--mask-ratio", type=float, default=0.6)
    ap.add_argument("--w-stat", type=float, default=W_STAT_DEFAULT)
    ap.add_argument("--w-consist", type=float, default=W_CONSIST_DEFAULT)
    ap.add_argument("--w-vicreg", type=float, default=W_VICREG_DEFAULT)
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--d-model", type=int, default=128)
    ap.add_argument("--log-every", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[{time.strftime('%H:%M:%S')}] device={dev} objective=SAS", flush=True)

    if args.memmap:
        ds = MemmapDataset(args.memmap, split=args.split, labeled=False)
        nw = 0
    else:
        ds = ShardDataset(args.shard_dir, split=args.split, labeled=False,
                          glob_pat=args.glob)
        nw = args.num_workers
    dl = DataLoader(ds, batch_size=args.batch_size, shuffle=True,
                    num_workers=nw, drop_last=True,
                    pin_memory=(dev == "cuda"),
                    persistent_workers=(nw > 0))
    print(f"  pretrain windows: {len(ds)}", flush=True)

    enc = AlignEncoder(d_model=args.d_model).to(dev)
    head = StatHead(args.d_model).to(dev)
    proj = Projector(args.d_model).to(dev)
    norm = FeatureNormalizer().to(dev)
    params = (list(enc.parameters()) + list(head.parameters())
              + list(proj.parameters()))
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=1e-4)
    total_steps = args.epochs * max(1, len(dl))
    sched = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=args.lr, total_steps=total_steps, pct_start=0.05)

    use_amp = (dev == "cuda")
    cap = torch.cuda.get_device_capability() if use_amp else (0, 0)
    amp_dtype = torch.bfloat16 if (use_amp and cap[0] >= 8) else torch.float16
    scaler = torch.amp.GradScaler("cuda",
                                  enabled=(use_amp and amp_dtype == torch.float16))
    if use_amp:
        print(f"  AMP dtype={amp_dtype}", flush=True)

    step, hist = 0, []
    for ep in range(args.epochs):
        enc.train(); head.train(); proj.train()
        for x in dl:
            x = x.to(dev, non_blocking=True)
            # statistics are computed in fp32 OUTSIDE autocast: several of the
            # twelve are ratios and maxima that lose meaningful precision in
            # fp16, and they are the regression target.
            with torch.no_grad():
                f = batch_features(x)
                norm.observe(f)
                tgt = norm(f)
            with torch.autocast(device_type=dev.split(":")[0], dtype=amp_dtype,
                                enabled=use_amp):
                xa = occlude(x, args.mask_ratio)
                xb = occlude(x, args.mask_ratio)
                za, zb = enc(xa), enc(xb)
                loss, parts = sas_loss(
                    head(za).float(), head(zb).float(), tgt,
                    proj(za), proj(zb),
                    w_stat=args.w_stat, w_consist=args.w_consist,
                    w_vicreg=args.w_vicreg)
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(opt); scaler.update(); sched.step()
            if step % args.log_every == 0:
                print(f"  ep{ep} step{step} loss={loss.item():.3f} "
                      f"stat={parts['stat']:.3f} consist={parts['consist']:.3f} "
                      f"vic={parts['vicreg']:.3f}", flush=True)
                hist.append({"step": step, "loss": float(loss), **parts})
            step += 1
        torch.save({"encoder": enc.state_dict(), "epoch": ep,
                    "d_model": args.d_model, "objective": "sas",
                    "feat_mean": norm.mean.cpu(), "feat_var": norm.var.cpu()},
                   args.out)
        with open(args.out + ".hist.json", "w") as fh:
            json.dump(hist, fh)
        if hist:
            print(f"[{time.strftime('%H:%M:%S')}] epoch {ep} done "
                  f"loss={hist[-1]['loss']:.3f} (ckpt saved)", flush=True)
    print(f"[{time.strftime('%H:%M:%S')}] saved encoder -> {args.out}", flush=True)


if __name__ == "__main__":
    main()
