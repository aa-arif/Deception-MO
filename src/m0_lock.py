"""M0 convention lock (CPU). Scores released probes on our extracted features under every
candidate (layer-index convention × pooling) and compares with sweep.json.

Candidates for a probe that says `layer = L`:
    hsL       HF hidden_states[L]   == output of decoder layer L-1   (file L{L-1}.npy)
    outL      output of decoder layer L == HF hidden_states[L+1]     (file L{L}.npy)
    postnorm  post-final-norm output (what HF hidden_states[64] actually is)  (Lnorm.npy; L=63 only)
Tests:
    A. validation metrics (AUROC, TPR/FPR/BA at the stored threshold) on the full non-ambiguous
       split, on the first-500-per-class subset, and the mean±sd over random 500/500 subsamples
       (sweep.json metrics are on a 500/500 subsample: TPR/FPR are multiples of 1/500, 1/499).
    B. DYL only: recompute diff-of-means from the train split -> cosine with released `direction`.
    C. lr/mlp checkpoints: stored dataset_mean/std vs train-split feature mean/std.
    D. calibration: 99th percentile of per-sample Alpaca scores vs stored threshold; FPR of the
       stored threshold on our Alpaca scores.
Writes results/m0/lock/<family>__<organism>.{json,md}.
"""
from __future__ import annotations

import argparse, json, os
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import lie_detectors  # noqa: F401  (installs the legacy unpickling alias)
from lie_detectors import load_probe
from sklearn.metrics import roc_auc_score

HF = os.environ.get("HF_HOME", "/lambda/nfs/lieprobes/hf")
REPO = Path("/lambda/nfs/lieprobes/repo")
POOLINGS = ["mean", "mean_imend", "first", "last", "imend"]
FAM = {
    "dyl": dict(val="dyl_validate_varied_deception", alpaca="dyl_alpaca_validate", train="dyl_train_city_countries",
                poolings=["first", "mean", "last", "imend"], layers=[38, 44, 63]),
    "apollo": dict(val="varied_deception_validation", alpaca="alpaca", train=None,
                   poolings=["mean", "mean_imend", "last", "first"], layers=[13, 38, 44, 57]),
}


def snapshot(repo_id):
    d = Path(HF) / "hub" / ("models--" + repo_id.replace("/", "--")) / "snapshots"
    return sorted(d.glob("*"), key=os.path.getmtime)[-1]


class Feats:
    def __init__(self, root: Path):
        self.root = root
        self.idx = pd.read_parquet(root / "index.parquet")
        self.meta = json.load(open(root / "meta.json"))
        self._cache = {}

    def get(self, key, pooling) -> np.ndarray:
        f = self.root / f"L{key}.npy"
        if not f.exists():
            return None
        if key not in self._cache:
            self._cache[key] = np.load(f, mmap_mode="r")
        return np.asarray(self._cache[key][:, POOLINGS.index(pooling), :], dtype=np.float32)


def candidates(L: int):
    c = {"hsL": L - 1, "outL": L}
    if L == 63:
        c["postnorm"] = "norm"
    return c


def score(probe, X: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        return probe(torch.from_numpy(np.ascontiguousarray(X))).numpy().astype(np.float64)


def metrics(s, y, thr):
    ok = np.isfinite(s)
    s, y = s[ok], y[ok]
    if len(np.unique(y)) < 2:
        return None
    tpr = float(np.mean(s[y == 1] > thr)); fpr = float(np.mean(s[y == 0] > thr))
    return {"auroc": float(roc_auc_score(y, s)), "tpr": tpr, "fpr": fpr, "ba": (tpr + 1 - fpr) / 2, "n_lie": int((y == 1).sum()), "n_honest": int((y == 0).sum())}


def subsample_metrics(s, y, thr, rng, n=500, reps=200):
    lie = np.where(y == 1)[0]; hon = np.where(y == 0)[0]
    first = np.concatenate([lie[:n], hon[:n]])
    m_first = metrics(s[first], y[first], thr)
    boots = []
    for _ in range(reps):
        sel = np.concatenate([rng.choice(lie, min(n, len(lie)), replace=False), rng.choice(hon, min(n, len(hon)), replace=False)])
        m = metrics(s[sel], y[sel], thr)
        if m: boots.append(m)
    agg = {k: (float(np.mean([b[k] for b in boots])), float(np.std([b[k] for b in boots]))) for k in ["auroc", "ba", "tpr", "fpr"]}
    return m_first, agg


def cos(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=list(FAM), required=True)
    ap.add_argument("--organism", default="gender_secret_female")
    ap.add_argument("--features", default=str(REPO / "features" / "qwen3.6-27b"))
    ap.add_argument("--layers", nargs="*", type=int, default=None)
    ap.add_argument("--extra-checkpoints", nargs="*", default=[], help="additional checkpoint safe_names to score")
    ap.add_argument("--include-ambiguous", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    F = FAM[a.family]
    layers = a.layers or F["layers"]
    rng = np.random.default_rng(a.seed)
    P = snapshot(f"ai-safety-institute/{a.family}-qwen-qwen3.6-27b__ai-safety-institute-qwen3.6-27b-{a.organism}")
    sweep = json.load(open(P / "sweep.json"))
    S = {e["safe_name"]: e for e in sweep["sweep"]}
    froot = Path(a.features) / a.organism
    val = Feats(froot / F["val"]); alp = Feats(froot / F["alpaca"])
    train = Feats(froot / F["train"]) if F["train"] and (froot / F["train"]).exists() else None
    print(f"family={a.family} organism={a.organism} default={sweep['default_filename']} | val n={len(val.idx)} alpaca n={len(alp.idx)} train n={len(train.idx) if train else None}")

    # checkpoints to test: dim at each layer, best mlp + best lr at each layer, default, extras
    names = []
    for L in layers:
        names.append(f"l_{L}_ar_dim")
        for arch in ["lr", "mlp"]:
            c = [e for e in sweep["sweep"] if e["hyperparams"]["layer"] == L and e["hyperparams"]["probe_architecture"] == arch]
            if c:
                names.append(max(c, key=lambda e: e["results"]["balanced_accuracy"])["safe_name"])
    names += [sweep["default_filename"]] + a.extra_checkpoints
    names = list(dict.fromkeys(n for n in names if n in S))

    yv = val.idx["label"].map({"lie": 1, "honest": 0}).to_numpy(dtype=float)
    keep_v = np.isfinite(yv) if not a.include_ambiguous else np.ones(len(yv), bool)
    ya = alp.idx["label"].to_numpy()
    keep_a = (ya == "honest") | a.include_ambiguous
    if train is not None:
        yt = train.idx["label"].map({"lie": 1, "honest": 0}).to_numpy(dtype=float)
        keep_t = np.isfinite(yt)

    rows = []; out = {"family": a.family, "organism": a.organism, "default": sweep["default_filename"], "results": []}
    for name in names:
        e = S[name]; L = e["hyperparams"]["layer"]; arch = e["hyperparams"]["probe_architecture"]
        probe = load_probe(P / f"{name}.pt"); thr = float(probe.threshold)
        sd = probe.state_dict()
        for cand, key in candidates(L).items():
            for pool in F["poolings"]:
                Xv = val.get(key, pool)
                if Xv is None:
                    continue
                sv = score(probe, Xv); m_full = metrics(sv[keep_v], yv[keep_v], thr)
                if m_full is None:
                    continue
                m_first, boot = subsample_metrics(sv[keep_v], yv[keep_v], thr, rng)
                r = {"ckpt": name, "layer": L, "arch": arch, "cand": cand, "pool": pool, "sweep": e["results"],
                     "full": m_full, "first500": m_first, "boot500": boot}
                # D. calibration
                Xa = alp.get(key, pool)
                if Xa is not None:
                    sa = score(probe, Xa)[keep_a]; sa = sa[np.isfinite(sa)]
                    r["calib"] = {"thr_stored": thr, "thr_p99_linear": float(np.percentile(sa, 99)), "thr_p99_higher": float(np.percentile(sa, 99, method="higher")),
                                  "fpr_of_stored_thr_on_alpaca": float(np.mean(sa > thr)), "n_alpaca": int(len(sa))}
                # B/C. train-split fingerprints
                if train is not None:
                    Xt = train.get(key, pool)
                    if Xt is not None:
                        fin = np.isfinite(Xt).all(1)
                        if arch == "dim":
                            d_hat = Xt[keep_t & fin & (yt == 1)].mean(0) - Xt[keep_t & fin & (yt == 0)].mean(0)
                            r["direction_cos"] = cos(d_hat, sd["direction"].numpy())
                            r["direction_cos_incl_ambig"] = cos(Xt[fin & (yt == 1)].mean(0) - Xt[fin & (yt == 0)].mean(0), sd["direction"].numpy())
                        else:
                            m_hat = Xt[keep_t & fin].mean(0); s_hat = Xt[keep_t & fin].std(0)
                            m0 = sd["dataset_mean"].numpy(); s0 = sd["dataset_std"].numpy()
                            r["mean_rel_err"] = float(np.linalg.norm(m_hat - m0) / np.linalg.norm(m0)); r["mean_cos"] = cos(m_hat, m0)
                            r["std_rel_err"] = float(np.linalg.norm(s_hat - s0) / np.linalg.norm(s0))
                            r["mean_d3994"] = (float(m_hat[3994]), float(m0[3994]))
                out["results"].append(r); rows.append(r)
                print(f"{name:42s} {cand:8s} {pool:10s} AUROC full={m_full['auroc']:.4f} first500={m_first['auroc']:.4f} boot={boot['auroc'][0]:.4f}±{boot['auroc'][1]:.4f} | sweep={e['results']['auroc']:.4f} "
                      f"|| BA full={m_full['ba']:.3f} first500={m_first['ba']:.3f} sweep={e['results']['balanced_accuracy']:.3f} | TPR/FPR full={m_full['tpr']:.3f}/{m_full['fpr']:.3f} sweep={e['results']['tpr']:.3f}/{e['results']['fpr']:.3f}"
                      + (f" | dir_cos={r['direction_cos']:.4f}" if "direction_cos" in r else "") + (f" | mean_rel_err={r['mean_rel_err']:.4f}" if "mean_rel_err" in r else "")
                      + (f" | thr stored={thr:.2f} p99={r['calib']['thr_p99_linear']:.2f} fpr@stored={r['calib']['fpr_of_stored_thr_on_alpaca']:.4f}" if "calib" in r else ""), flush=True)
    od = REPO / "results" / "m0" / "lock"; od.mkdir(parents=True, exist_ok=True)
    tag = f"{a.family}__{a.organism}" + ("__incl_ambig" if a.include_ambiguous else "")
    (od / f"{tag}.json").write_text(json.dumps(out, indent=1))
    # markdown summary
    md = [f"# Lock results: {a.family} / {a.organism} (default {sweep['default_filename']})", "",
          "| ckpt | cand | pool | AUROC full | AUROC first500 | AUROC boot500 | sweep AUROC | BA full | BA first500 | sweep BA | TPR/FPR full | sweep TPR/FPR | dir cos | mean rel err | thr stored / p99 | FPR@stored |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        c = r.get("calib", {})
        md.append(f"| {r['ckpt']} | {r['cand']} | {r['pool']} | {r['full']['auroc']:.4f} | {r['first500']['auroc']:.4f} | {r['boot500']['auroc'][0]:.4f}±{r['boot500']['auroc'][1]:.4f} | {r['sweep']['auroc']:.4f} | {r['full']['ba']:.3f} | {r['first500']['ba']:.3f} | {r['sweep']['balanced_accuracy']:.3f} | {r['full']['tpr']:.3f}/{r['full']['fpr']:.3f} | {r['sweep']['tpr']:.3f}/{r['sweep']['fpr']:.3f} | "
                  f"{r.get('direction_cos', float('nan')):.4f} | {r.get('mean_rel_err', float('nan')):.4f} | {c.get('thr_stored', float('nan')):.2f} / {c.get('thr_p99_linear', float('nan')):.2f} | {c.get('fpr_of_stored_thr_on_alpaca', float('nan')):.4f} |")
    (od / f"{tag}.md").write_text("\n".join(md))
    print("wrote", od / f"{tag}.md")


if __name__ == "__main__":
    main()
