#!/usr/bin/env python3
"""Stage 1 — self-supervised pretraining of AlignEncoder (MAE + VICReg).

Reads unlabeled alignment tensors (precomputed .npz shards, TRAIN chroms
only) and optimizes a combined masked-reconstruction + VICReg objective.
Saves the encoder weights for Stage-2 fine-tuning.
"""
from __future__ import annotations
import argparse, os, time, json
import numpy as np
import torch
from torch.utils.data import DataLoader

from alignssl.data import ShardDataset, MemmapDataset
from alignssl.encoder import AlignEncoder
from alignssl.ssl import (MAEDecoder, column_targets, mae_mask, mae_loss,
                          Projector, vicreg_loss, subsample_rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-dir", required=True)
    ap.add_argument("--memmap", default=None,
                    help="memmap prefix (from build_memmap.py); if set, uses "
                         "MemmapDataset with num_workers=0 (no CUDA-fork hang)")
    ap.add_argument("--out", required=True, help="encoder checkpoint path")
    ap.add_argument("--split", default="train")
    ap.add_argument("--glob", default="*.npz", help="shard filename pattern")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--mask-ratio", type=float, default=0.6)
    ap.add_argument("--w-mae", type=float, default=1.0)
    ap.add_argument("--w-vicreg", type=float, default=1.0)
    ap.add_argument("--view-keep", type=float, default=0.5,
                    help="row keep-fraction for the second (coverage) view")
    ap.add_argument("--num-workers", type=int, default=8)
    ap.add_argument("--d-model", type=int, default=128)
    ap.add_argument("--log-every", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[{time.strftime('%H:%M:%S')}] device={dev}", flush=True)

    if args.memmap:
        ds = MemmapDataset(args.memmap, split=args.split, labeled=False)
        nw = 0  # memmap reads from page cache in-process; no fork
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
    dec = MAEDecoder(args.d_model).to(dev)
    proj = Projector(args.d_model).to(dev)
    params = list(enc.parameters()) + list(dec.parameters()) + list(proj.parameters())
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=1e-4)
    total_steps = args.epochs * max(1, len(dl))
    sched = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=args.lr, total_steps=total_steps, pct_start=0.05)
    use_amp = (dev == "cuda")
    # bf16 only on Ampere+ (sm_80+, e.g. A100). Turing (T4, sm_75) reports
    # is_bf16_supported()=True but emulates bf16 slowly; use fp16 tensor cores.
    cap = torch.cuda.get_device_capability() if use_amp else (0, 0)
    amp_dtype = torch.bfloat16 if (use_amp and cap[0] >= 8) else torch.float16
    scaler = torch.amp.GradScaler("cuda", enabled=(use_amp and amp_dtype == torch.float16))
    if use_amp:
        print(f"  AMP dtype={amp_dtype}", flush=True)

    step = 0
    hist = []
    for ep in range(args.epochs):
        enc.train(); dec.train(); proj.train()
        for x in dl:
            x = x.to(dev, non_blocking=True)
            with torch.autocast(device_type=dev.split(":")[0], dtype=amp_dtype,
                                enabled=use_amp):
                # --- MAE branch ---
                xm, colmask = mae_mask(x, args.mask_ratio)
                _, cols = enc(xm, return_cols=True)
                pred = dec(cols)
                tgt = column_targets(x)
                l_mae = mae_loss(pred, tgt, colmask)
                # --- VICReg branch: two coverage views ---
                v1 = subsample_rows(x, 1.0)
                v2 = subsample_rows(x, args.view_keep)
                z1 = proj(enc(v1)); z2 = proj(enc(v2))
                l_vic, _vic_parts = vicreg_loss(z1, z2)
                loss = args.w_mae * l_mae + args.w_vicreg * l_vic
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(opt); scaler.update(); sched.step()
            if step % args.log_every == 0:
                print(f"  ep{ep} step{step} loss={loss.item():.3f} "
                      f"mae={float(l_mae):.3f} vic={float(l_vic):.3f}",
                      flush=True)
                hist.append({"step": step, "loss": float(loss),
                             "mae": float(l_mae), "vic": float(l_vic)})
            step += 1
        torch.save({"encoder": enc.state_dict(), "epoch": ep,
                    "d_model": args.d_model}, args.out)
        with open(args.out + ".hist.json", "w") as f:
            json.dump(hist, f)
        if hist:
            print(f"[{time.strftime('%H:%M:%S')}] epoch {ep} done "
                  f"loss={hist[-1]['loss']:.3f} (ckpt saved)", flush=True)
    with open(args.out + ".hist.json", "w") as f:
        json.dump(hist, f)
    print(f"[{time.strftime('%H:%M:%S')}] saved encoder -> {args.out}", flush=True)


if __name__ == "__main__":
    main()
