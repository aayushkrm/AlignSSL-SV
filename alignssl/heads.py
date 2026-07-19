"""
Task heads + calibrated uncertainty for AlignSSL-SV (roadmap sections 5-6).

Fine-tuning heads (section 5):
    - deletion classifier (DEL vs no-DEL)  -> focal loss
    - genotype head (0/0, 0/1, 1/1)         -> cross-entropy
    - breakpoint regression (start, end offset within window) -> smooth-L1

Calibrated uncertainty (section 6, the second contribution):
    - deep-ensemble OR MC-dropout for epistemic uncertainty
    - temperature scaling for post-hoc calibration
    - conformal prediction wrapper for distribution-free coverage
Loss: L_ft = L_type(focal) + a*L_geno + b*L_bp(smoothL1) + g*L_uncert
"""
from __future__ import annotations
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class SVHeads(nn.Module):
    def __init__(self, d_model: int, p_drop: float = 0.2):
        super().__init__()
        self.drop = nn.Dropout(p_drop)  # kept active at test time for MC-dropout
        self.cls = nn.Linear(d_model, 2)        # DEL vs not
        self.geno = nn.Linear(d_model, 3)        # 0/0, 0/1, 1/1
        self.bp = nn.Linear(d_model, 2)          # start, end offsets (0..1 of W)

    def forward(self, z):
        z = self.drop(z)
        return {
            "cls_logits": self.cls(z),
            "geno_logits": self.geno(z),
            "bp": torch.sigmoid(self.bp(z)),
        }


def focal_loss(logits, target, gamma: float = 2.0, alpha=None):
    """Multi-class focal loss (Lin et al. 2017) for class imbalance."""
    logp = F.log_softmax(logits, dim=-1)
    p = logp.exp()
    ce = F.nll_loss(logp, target, weight=alpha, reduction="none")
    pt = p.gather(1, target.unsqueeze(1)).squeeze(1)
    return ((1 - pt) ** gamma * ce).mean()


def finetune_loss(out, batch, a=1.0, b=1.0, g=0.0, focal_gamma=2.0):
    """Combined fine-tuning loss. batch has 'label','geno','bp' targets;
    entries may be -1 / NaN where a sub-task label is absent (masked out)."""
    logs = {}
    lt = focal_loss(out["cls_logits"], batch["label"], gamma=focal_gamma)
    logs["type"] = lt.item()
    loss = lt
    if "geno" in batch and (batch["geno"] >= 0).any():
        m = batch["geno"] >= 0
        lg = F.cross_entropy(out["geno_logits"][m], batch["geno"][m])
        loss = loss + a * lg
        logs["geno"] = lg.item()
    if "bp" in batch:
        m = ~torch.isnan(batch["bp"]).any(dim=1)
        if m.any():
            lb = F.smooth_l1_loss(out["bp"][m], batch["bp"][m])
            loss = loss + b * lb
            logs["bp"] = lb.item()
    logs["total"] = loss.item()
    return loss, logs


# ----------------------- calibration -----------------------
class TemperatureScaler(nn.Module):
    """Post-hoc temperature scaling (Guo et al. 2017)."""

    def __init__(self):
        super().__init__()
        self.log_T = nn.Parameter(torch.zeros(1))

    def forward(self, logits):
        return logits / self.log_T.exp()

    def fit(self, logits, labels, max_iter=200, lr=0.01):
        logits = logits.detach()
        labels = labels.detach()
        opt = torch.optim.LBFGS([self.log_T], lr=lr, max_iter=max_iter)

        def closure():
            opt.zero_grad()
            loss = F.cross_entropy(self.forward(logits), labels)
            loss.backward()
            return loss

        opt.step(closure)
        return self.log_T.exp().item()


def mc_dropout_predict(model_forward, x, n_samples: int = 20):
    """Epistemic uncertainty via MC-dropout. model_forward(x)->cls_logits.
    Returns mean prob and predictive entropy."""
    probs = []
    for _ in range(n_samples):
        logits = model_forward(x)
        probs.append(F.softmax(logits, dim=-1))
    P = torch.stack(probs, 0)            # [S, B, K]
    mean = P.mean(0)                     # [B, K]
    entropy = -(mean * (mean + 1e-9).log()).sum(-1)   # total uncertainty
    # aleatoric = E[H(p)], epistemic = H(E[p]) - E[H(p)]
    aleatoric = -(P * (P + 1e-9).log()).sum(-1).mean(0)
    epistemic = entropy - aleatoric
    return {"prob": mean, "entropy": entropy,
            "aleatoric": aleatoric, "epistemic": epistemic}


def expected_calibration_error(probs, labels, n_bins: int = 15):
    """ECE (Naeini et al. 2015). probs: [N,K], labels: [N]."""
    conf, pred = probs.max(-1)
    conf = conf.detach().cpu().numpy()
    correct = (pred.detach().cpu() == labels.detach().cpu()).numpy().astype(float)
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    N = len(conf)
    for i in range(n_bins):
        m = (conf > bins[i]) & (conf <= bins[i + 1])
        if m.sum() > 0:
            ece += (m.sum() / N) * abs(correct[m].mean() - conf[m].mean())
    return float(ece)


class ConformalBinary:
    """Split-conformal for a positive-class score; guarantees marginal
    coverage 1 - alpha on exchangeable data (Vovk; Angelopoulos & Bates)."""

    def __init__(self, alpha: float = 0.1):
        self.alpha = alpha
        self.qhat = None

    def calibrate(self, scores_pos, labels):
        # nonconformity for the true label = 1 - score_of_true_class
        s = np.where(labels == 1, 1 - scores_pos, scores_pos)
        n = len(s)
        q = np.ceil((n + 1) * (1 - self.alpha)) / n
        self.qhat = np.quantile(s, min(q, 1.0), method="higher")
        return self.qhat

    def predict_set(self, scores_pos):
        """Return, per item, the set of admissible labels among {0,1}."""
        assert self.qhat is not None, "call calibrate() first"
        keep1 = (1 - scores_pos) <= self.qhat   # label 1 admissible
        keep0 = scores_pos <= self.qhat         # label 0 admissible
        return np.stack([keep0, keep1], axis=1)
