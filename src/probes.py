"""Probe estimators shared by M2–M6 (D16): lr (primary), dim and shrinkage diff-of-means (secondary)."""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.covariance import LedoitWolf
from sklearn.metrics import roc_auc_score
C_GRID = [1e-4, 1e-3, 1e-2, 1e-1, 1.0]

class DimProbe:
    name = "dim"
    def fit(self, X, y): self.d = X[y == 1].mean(0) - X[y == 0].mean(0); return self
    def score(self, X): return X @ self.d
    def direction(self): return self.d / np.linalg.norm(self.d)

class ShrinkProbe:
    """Whitened diff-of-means: w = Σ⁻¹ d with Σ the Ledoit–Wolf pooled within-class covariance."""
    name = "shrink"
    def fit(self, X, y):
        m1, m0 = X[y == 1].mean(0), X[y == 0].mean(0); Xc = np.vstack([X[y == 1] - m1, X[y == 0] - m0])
        lw = LedoitWolf(store_precision=True).fit(Xc); self.d = m1 - m0; self.w = lw.precision_ @ self.d; self.shrinkage = float(lw.shrinkage_); return self
    def score(self, X): return X @ self.w
    def direction(self): return self.w / np.linalg.norm(self.w)

class LRProbe:
    name = "lr"
    def __init__(self, C=1e-2): self.C = C
    def fit(self, X, y):
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-6
        self.m = LogisticRegression(C=self.C, max_iter=1000).fit((X - self.mu) / self.sd, y); return self
    def score(self, X): return self.m.decision_function((X - self.mu) / self.sd)
    def direction(self):
        w = self.m.coef_[0] / self.sd; return w / np.linalg.norm(w)

def make(est, C=None): return {"dim": DimProbe, "shrink": ShrinkProbe}[est]() if est != "lr" else LRProbe(C)

def auroc(y, s):
    ok = np.isfinite(s); return float(roc_auc_score(y[ok], s[ok])) if len(np.unique(y[ok])) == 2 else float("nan")
def thr_1pct(probe, Xa): s = probe.score(Xa); s = s[np.isfinite(s)]; return float(np.percentile(s, 99))
def ba_at(s, y, thr):
    tpr = float(np.mean(s[y == 1] > thr)); fpr = float(np.mean(s[y == 0] > thr)); return (tpr + 1 - fpr) / 2, tpr, fpr
def boot_auroc(s, y, n=1000, seed=0):
    rng = np.random.default_rng(seed); v = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) == 2: v.append(roc_auc_score(y[i], s[i]))
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
