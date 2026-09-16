"""M6 decomposition of each organism's lie signal into offset / rotation / novelty (directive 2026-09-16, item 5).
Per organism and pooling (Apollo: mean @L38; DYL: pred @L44), using the organism's own auditing set:
  d_org   raw diff-of-means lie direction (lie − honest)
  f       offset / fine-tune fingerprint direction: mean(organism Alpaca) − mean(base Alpaca)
  B       base-lie subspace: span{prompted-lie direction of the base model (Varied Deception, raw diff-of-means),
          released base dim probe direction at the layer (if present)}
Decomposition of d_org (unit): fraction of ‖d‖² along f, along B (after removing f), and the residual = NOVELTY.
Functional version: AUROC of the organism's lies when scoring with (i) f alone, (ii) the projection of d_org on B,
(iii) the novel residual, (iv) d_org itself; and the CORAL gain from T1 as the ROTATION indicator (second-moment).
Writes results/m6/decomposition.md + .json."""
import json, os, glob
from pathlib import Path
import numpy as np, pandas as pd
import lie_detectors  # noqa
from lie_detectors import load_probe
from probes import auroc, boot_auroc
HF = os.environ.get("HF_HOME", "/lambda/nfs/lieprobes/hf"); REPO = Path("/lambda/nfs/lieprobes/repo"); F = REPO / "features/qwen3.6-27b"
ORGS = {"gender_secret_female": "gender_secret", "gender_secret_male": "gender_secret", "eval_sandbagger": "sandbagging_games_updated", "ab_animal_welfare": "audit_bench_updated", "ab_contextual_optimism": "audit_bench_updated", "ab_hallucinates_citations": "audit_bench_updated", "ab_self_promotion": "audit_bench_updated"}
SHORT = {"gender_secret_female": "GS-F", "gender_secret_male": "GS-M", "eval_sandbagger": "SB", "ab_animal_welfare": "AW", "ab_contextual_optimism": "CO", "ab_hallucinates_citations": "HC", "ab_self_promotion": "SP"}
CFG = [("apollo", 38, "mean", "alpaca", "", "varied_deception"), ("dyl", 44, "pred", "dyl_alpaca_validate", "dyl_", "dyl_validate_varied_deception")]
def snap(r): return sorted(glob.glob(f"{HF}/hub/models--{r.replace('/', '--')}/snapshots/*"), key=os.path.getmtime)[-1]
def load(org, split, L, pool):
    d = F / org / split; meta = json.load(open(d / "meta.json")); pi = meta["poolings"].index(pool)
    return np.load(d / f"L{L}.npy", mmap_mode="r")[:, pi, :].astype(np.float32), pd.read_parquet(d / "index.parquet")
def unit(v): return v / (np.linalg.norm(v) + 1e-12)
def proj_out(v, basis):  # remove the span of orthonormal basis rows
    return v - basis.T @ (basis @ v)
def orth(vs):
    Q = []
    for v in vs:
        r = proj_out(v, np.array(Q)) if Q else v
        if np.linalg.norm(r) > 1e-6 * np.linalg.norm(v): Q.append(unit(r))
    return np.array(Q)
out = {}; md = ["# M6 — offset / rotation / novelty decomposition of each organism's lie direction", "",
                "d = organism's raw diff-of-means lie direction on its auditing set. f = fine-tune fingerprint (organism − base Alpaca mean). B = base-lie",
                "subspace (base prompted-lie direction from Varied Deception + released base dim probe). Fractions = share of ‖d‖² along f, along B (f removed),",
                "and the residual (novel). AUROCs = the organism's lies vs honest scored along that component alone. Rotation = T1 CORAL gain (M4).", ""]
for fam, L, pool, cal, prefix, vd in CFG:
    Xb, ib = load("base", cal, L, pool); mub = Xb[np.isfinite(Xb).all(1) & (ib["label"].values == "honest")].mean(0)
    Xv, iv = load("base", vd, L, pool); yv = iv["label"].map({"lie": 1.0, "honest": 0.0}).to_numpy(float); okv = np.isfinite(yv) & np.isfinite(Xv).all(1)
    prompted = Xv[okv & (yv == 1)].mean(0) - Xv[okv & (yv == 0)].mean(0)
    try: base_dim = load_probe(Path(snap(f"ai-safety-institute/{fam}-qwen-qwen3.6-27b")) / f"l_{L}_ar_dim.pt").state_dict()["direction"].numpy()
    except Exception: base_dim = None
    Bvecs = [prompted] + ([base_dim] if base_dim is not None else []); md += [f"## {fam} pooling `{pool}`, layer {L}", "", "| organism | ‖d‖ | frac along f (offset) | frac along B (base-lie) | frac novel | AUROC: f alone | AUROC: B-component | AUROC: novel component | AUROC: d | T1 raw → CORAL (rotation) | ∠(d, f) | ∠(d, prompted) |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for org, split in ORGS.items():
        X, idx = load(org, prefix + split, L, pool); y = idx["label"].map({"lie": 1.0, "honest": 0.0}).to_numpy(float); ok = np.isfinite(y) & np.isfinite(X).all(1); X, y = X[ok], y[ok]
        Xa, ia = load(org, cal, L, pool); f = Xa[np.isfinite(Xa).all(1) & (ia["label"].values == "honest")].mean(0) - mub
        d = X[y == 1].mean(0) - X[y == 0].mean(0); n2 = float(d @ d)
        fu = unit(f); c_f = d @ fu; d1 = d - c_f * fu
        Bq = orth([proj_out(v, fu[None, :]) for v in Bvecs]); cB = Bq @ d1; dB = Bq.T @ cB; dn = d1 - dB
        fr_f, fr_B, fr_n = c_f**2 / n2, float(cB @ cB) / n2, float(dn @ dn) / n2
        sc = lambda w: auroc(y, X @ unit(w)); t1 = json.load(open(REPO / f"results/m4/t1/{fam}/{org}.json"))["variants"]
        r = dict(norm_d=float(np.sqrt(n2)), frac_offset=fr_f, frac_base_lie=fr_B, frac_novel=fr_n, auroc_f=sc(f), auroc_B=(sc(dB) if np.linalg.norm(dB) > 0 else float("nan")), auroc_novel=sc(dn), auroc_d=sc(d), t1_raw=t1["raw"]["auroc"], t1_coral=t1["coral"]["auroc"], angle_d_f=float(np.degrees(np.arccos(np.clip(unit(d) @ fu, -1, 1)))), angle_d_prompted=float(np.degrees(np.arccos(np.clip(unit(d) @ unit(prompted), -1, 1)))))
        out[f"{fam}_{org}"] = r
        md.append(f"| {SHORT[org]} | {r['norm_d']:.1f} | {fr_f:.3f} | {fr_B:.3f} | {fr_n:.3f} | {r['auroc_f']:.3f} | {r['auroc_B']:.3f} | {r['auroc_novel']:.3f} | {r['auroc_d']:.3f} | {r['t1_raw']:.2f} → {r['t1_coral']:.2f} | {r['angle_d_f']:.0f}° | {r['angle_d_prompted']:.0f}° |")
    md.append("")
md += ["Reading: 'novel' is the part of the organism's lie direction outside the fingerprint and the base-lie subspace; its AUROC alone tells whether the",
       "organism's lies are separable by something the base model's lie geometry does not contain. A large 'offset' fraction with AUROC(f) ≈ 0.5 means the",
       "fingerprint direction is big but not discriminative (the fine-tune moved all activations, honest and lie alike)."]
(REPO / "results/m6/decomposition.json").write_text(json.dumps(out, indent=1, default=float)); (REPO / "results/m6/decomposition.md").write_text("\n".join(md) + "\n"); print("\n".join(md))
