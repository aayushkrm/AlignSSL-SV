"""AlignSSL vs DeepSV under the corrected protocol.

The project's primary claim is that AlignSSL's learned alignment tensor
detects deletions better than DeepSV's fixed RGB pileup. This script tests
exactly that contrast -- and, where it fails to reject, reports what effect
size the design could have detected, so a null is not read as equivalence.
"""
import argparse, glob, json, os
import numpy as np
import pandas as pd
from scipy import stats

ARMS = {"AlignSSL-pretrained": ("pre", "pretrained"),
        "AlignSSL-scratch":    ("scr", "scratch"),
        "DeepSV-representation": ("dsv", "deepsv")}

def load(json_dir, bench, stem, key, metric):
    """{frac: {seed: value}} for one arm."""
    out = {}
    for p in sorted(glob.glob(os.path.join(json_dir, f"f_{bench}_{stem}_seed*.json"))):
        seed = int(p.split("seed")[-1].split(".")[0])
        for r in json.load(open(p))["label_efficiency"]:
            out.setdefault(r["frac"], {})[seed] = r[key][metric]
    return out

def budgets(json_dir, bench):
    p = sorted(glob.glob(os.path.join(json_dir, f"f_{bench}_dsv_seed*.json")))[0]
    return {r["frac"]: r["n"] for r in json.load(open(p))["label_efficiency"]}

def paired(a, b):
    """Paired stats on the seeds present in both arms."""
    common = sorted(set(a) & set(b))
    x, y = np.array([a[s] for s in common]), np.array([b[s] for s in common])
    d = x - y
    n = len(d)
    sd = d.std(ddof=1) if n > 1 else np.nan
    t, p = stats.ttest_rel(x, y) if n > 2 else (np.nan, np.nan)
    # smallest true difference this design detects at 80% power, two-sided 0.05
    mde = (stats.t.ppf(0.975, n - 1) + stats.t.ppf(0.80, n - 1)) * sd / np.sqrt(n) if n > 2 else np.nan
    return dict(n_seeds=n, mean_a=x.mean(), mean_b=y.mean(), diff=d.mean(),
                diff_sd=sd, t=t, p=p, mde80=mde,
                ci_lo=d.mean() - stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n) if n > 2 else np.nan,
                ci_hi=d.mean() + stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n) if n > 2 else np.nan)

def holm(ps):
    ps = np.asarray(ps, float)
    ok = ~np.isnan(ps)
    adj = np.full_like(ps, np.nan)
    idx = np.argsort(ps[ok]); m = ok.sum()
    run, prev = np.empty(m), 0.0
    for k, i in enumerate(idx):
        prev = max(prev, min(1.0, (m - k) * ps[ok][i]))
        run[i] = prev
    adj[ok] = run
    return adj

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-dir", default="../handoff/deep")
    ap.add_argument("--out", default="results/table20_alignssl_vs_deepsv.csv")
    a = ap.parse_args()

    rows = []
    for bench, bname in (("uni", "uniform"), ("hn", "candidate-filtered")):
        bud = budgets(a.json_dir, bench)
        for metric in ("auprc", "roc_auc", "f1_at_tau"):
            dsv = load(a.json_dir, bench, "dsv", "deepsv", metric)
            for arm, (stem, key) in ARMS.items():
                if arm == "DeepSV-representation":
                    continue
                cur = load(a.json_dir, bench, stem, key, metric)
                for frac in sorted(set(cur) & set(dsv)):
                    r = paired(cur[frac], dsv[frac])
                    rows.append(dict(benchmark=bname, metric=metric, arm=arm,
                                     label_frac=frac, n_labelled=bud[frac], **r))
    df = pd.DataFrame(rows)
    # Holm within (benchmark, metric) family -- the sweep each cell was selected from
    df["p_holm"] = np.nan
    for (b, m), g in df.groupby(["benchmark", "metric"]):
        df.loc[g.index, "p_holm"] = holm(g["p"].values)
    df["verdict"] = np.where(df.p_holm < 0.05,
                             np.where(df["diff"] > 0, "AlignSSL better", "DeepSV better"),
                             "not separated")
    for c in ("mean_a", "mean_b", "diff", "diff_sd", "mde80", "ci_lo", "ci_hi"):
        df[c] = df[c].round(4)
    for c in ("t", "p", "p_holm"):
        df[c] = df[c].map(lambda v: float(f"{v:.4g}") if pd.notna(v) else v)
    df.to_csv(a.out, index=False)
    print(f"wrote {a.out}  rows={len(df)}")
    print(df[df.metric == "auprc"][["benchmark","arm","label_frac","n_labelled",
                                    "mean_a","mean_b","diff","p","p_holm","mde80","verdict"]]
          .to_string(index=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
