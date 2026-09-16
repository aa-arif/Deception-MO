"""M6 geometry (D16: shrinkage diff-of-means directions). Per family/layer:
  - d_i: shrinkage direction of organism i fitted on its own auditing set (graded labels)
  - 7×7 cosine matrix of unit directions; pairwise transfer AUROC(i→j): organism i's shrinkage probe scored
    on organism j's auditing features; Spearman(transfer_ij, cos_ij) over the 42 ordered pairs with a
    permutation test (10 000 joint row/column permutations of the organism labels of the cosine matrix)
  - SVD of the stacked unit directions (singular values, explained-variance fractions)
  - angles (degrees) of each d_i to: the prompted-lie direction (base model, varied_deception, same pooling/
    layer, shrinkage), the released organism probe direction (dim checkpoint at the layer, if present) and
    the released base-model dim direction, and the fine-tune fingerprint f_i = mean(organism Alpaca) −
    mean(base Alpaca); plus cos(f_i, f_j) and cos(d_i, mean fingerprint).
Layers: apollo pooling L38 (released default) and L57 (M2 best); dyl pooling L44. Writes results/m6/geometry.md + .json."""
import json, os, glob
from pathlib import Path
import numpy as np, pandas as pd, torch
from scipy.stats import spearmanr
import lie_detectors  # noqa
from lie_detectors import load_probe
from probes import ShrinkProbe, auroc
HF = os.environ.get("HF_HOME", "/lambda/nfs/lieprobes/hf"); REPO = Path("/lambda/nfs/lieprobes/repo"); F = REPO / "features/qwen3.6-27b"
ORGS = {"gender_secret_female": "gender_secret", "gender_secret_male": "gender_secret", "eval_sandbagger": "sandbagging_games_updated", "ab_animal_welfare": "audit_bench_updated", "ab_contextual_optimism": "audit_bench_updated", "ab_hallucinates_citations": "audit_bench_updated", "ab_self_promotion": "audit_bench_updated"}
SHORT = {"gender_secret_female": "GS-F", "gender_secret_male": "GS-M", "eval_sandbagger": "SB", "ab_animal_welfare": "AW", "ab_contextual_optimism": "CO", "ab_hallucinates_citations": "HC", "ab_self_promotion": "SP"}
CFG = [("apollo", 38, "mean", "alpaca", ""), ("apollo", 57, "mean", "alpaca", ""), ("dyl", 44, "pred", "dyl_alpaca_validate", "dyl_")]
def snap(r): return sorted(glob.glob(f"{HF}/hub/models--{r.replace('/', '--')}/snapshots/*"), key=os.path.getmtime)[-1]
def load(org, split, L, pool):
    d = F / org / split; meta = json.load(open(d / "meta.json")); pi = meta["poolings"].index(pool)
    return np.load(d / f"L{L}.npy", mmap_mode="r")[:, pi, :].astype(np.float32), pd.read_parquet(d / "index.parquet")
def unit(v): return v / np.linalg.norm(v)
def ang(a, b): return float(np.degrees(np.arccos(np.clip(np.dot(unit(a), unit(b)), -1, 1))))
def released_dim(repo, L):
    try: P = Path(snap(repo)); p = P / f"l_{L}_ar_dim.pt"; return load_probe(p).state_dict()["direction"].numpy() if p.exists() else None
    except Exception: return None
out = {}; md = ["# M6 — geometry of organism lie directions (shrinkage diff-of-means, D16)", ""]
for fam, L, pool, cal, prefix in CFG:
    key = f"{fam}_L{L}"; print("==", key, flush=True)
    D = {}; probes = {}
    for org, split in ORGS.items():
        X, idx = load(org, prefix + split, L, pool); y = idx["label"].map({"lie": 1.0, "honest": 0.0}).to_numpy(float); ok = np.isfinite(y) & np.isfinite(X).all(1)
        D[org] = (X[ok], y[ok]); probes[org] = ShrinkProbe().fit(X[ok], y[ok])
    names = list(ORGS); U = np.stack([probes[o].direction() for o in names]); cos = U @ U.T
    T = np.full((7, 7), np.nan)
    for i, oi in enumerate(names):
        for j, oj in enumerate(names):
            T[i, j] = auroc(D[oj][1], probes[oi].score(D[oj][0]))
    off = ~np.eye(7, dtype=bool); rho = spearmanr(T[off], cos[off]).statistic
    rng = np.random.default_rng(0); null = []
    for _ in range(10000):
        p = rng.permutation(7); null.append(spearmanr(T[off], cos[p][:, p][off]).statistic)
    pval = float(np.mean(np.abs(null) >= abs(rho)))
    s = np.linalg.svd(U, compute_uv=False); ev = s**2 / (s**2).sum()
    # reference directions
    Xv, iv = load("base", "varied_deception" if fam == "apollo" else "dyl_validate_varied_deception", L, pool); yv = iv["label"].map({"lie": 1.0, "honest": 0.0}).to_numpy(float); okv = np.isfinite(yv) & np.isfinite(Xv).all(1)
    prompted = ShrinkProbe().fit(Xv[okv], yv[okv]).direction()
    Xb, ib = load("base", cal, L, pool); mub = Xb[np.isfinite(Xb).all(1) & (ib["label"].values == "honest")].mean(0)
    fp = {}
    for org in names:
        Xa, ia = load(org, cal, L, pool); fp[org] = Xa[np.isfinite(Xa).all(1) & (ia["label"].values == "honest")].mean(0) - mub
    Fm = np.stack([unit(fp[o]) for o in names]); fcos = Fm @ Fm.T; mean_fp = unit(np.mean([fp[o] for o in names], 0))
    base_dim = released_dim(f"ai-safety-institute/{fam}-qwen-qwen3.6-27b", L)
    rel = {org: released_dim(f"ai-safety-institute/{fam}-qwen-qwen3.6-27b__ai-safety-institute-qwen3.6-27b-{org}", L) for org in names}
    rows = []
    for i, org in enumerate(names):
        rows.append(dict(organism=org, angle_prompted=ang(U[i], prompted), angle_released_org_dim=(ang(U[i], rel[org]) if rel[org] is not None else None), angle_released_base_dim=(ang(U[i], base_dim) if base_dim is not None else None), angle_fingerprint=ang(U[i], fp[org]), angle_mean_fingerprint=ang(U[i], mean_fp), fingerprint_norm=float(np.linalg.norm(fp[org])), shrinkage=probes[org].shrinkage))
    out[key] = dict(names=names, cos=cos.tolist(), transfer=T.tolist(), spearman=float(rho), perm_p=pval, singular_values=s.tolist(), explained=ev.tolist(), fingerprint_cos=fcos.tolist(), rows=rows, angle_prompted_vs_base_dim=(ang(prompted, base_dim) if base_dim is not None else None))
    sh = [SHORT[o] for o in names]
    md += [f"## {fam} pooling `{pool}`, layer {L}", "", "Cosine between organism directions (upper) / transfer AUROC i→j (row = trained on i):", "", "| | " + " | ".join(sh) + " |", "|---|" + "---|" * 7]
    for i in range(7): md.append(f"| **{sh[i]}** | " + " | ".join(f"{cos[i, j]:+.2f} / {T[i, j]:.2f}" if i != j else f"1 / {T[i, i]:.2f}" for j in range(7)) + " |")
    md += ["", f"Spearman(transfer AUROC, cosine) over 42 ordered pairs: ρ = {rho:.3f}, permutation p = {pval:.4f} (10 000 joint permutations).",
           f"SVD of the 7 unit directions: singular values {np.round(s, 2).tolist()}; explained fractions {np.round(ev, 3).tolist()} (first component {ev[0]:.2f}; isotropic would be 0.14 each).", "",
           "| organism | ∠ prompted-lie dir | ∠ released organism dim | ∠ released base dim | ∠ own fingerprint | ∠ mean fingerprint | ‖fingerprint‖ | LW shrinkage |", "|---|---|---|---|---|---|---|---|"]
    for r in rows: md.append(f"| {SHORT[r['organism']]} | {r['angle_prompted']:.1f}° | " + (f"{r['angle_released_org_dim']:.1f}°" if r["angle_released_org_dim"] is not None else "–") + " | " + (f"{r['angle_released_base_dim']:.1f}°" if r["angle_released_base_dim"] is not None else "–") + f" | {r['angle_fingerprint']:.1f}° | {r['angle_mean_fingerprint']:.1f}° | {r['fingerprint_norm']:.1f} | {r['shrinkage']:.3f} |")
    md += ["", "Fingerprint cosines (organism − base Alpaca mean), upper triangle: " + ", ".join(f"{sh[i]}·{sh[j]} {fcos[i, j]:+.2f}" for i in range(7) for j in range(i + 1, 7)), "", f"(prompted-lie vs released base dim: {out[key]['angle_prompted_vs_base_dim']:.1f}°)" if base_dim is not None else "", ""]
(REPO / "results/m6").mkdir(exist_ok=True); (REPO / "results/m6/geometry.json").write_text(json.dumps(out, indent=1)); (REPO / "results/m6/geometry.md").write_text("\n".join(md) + "\n"); print("\n".join(md))
