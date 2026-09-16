"""M8 Aletheia cross-pipeline transfer (Burst 2 item 4, CPU; LIEPROBES_TAG=qwen3.5-27b). Features: features/qwen3.5-27b/
<aletheia model>/{aletheia_instructed, aletheia_varied, dyl_aletheia_*, alpaca, dyl_alpaca_validate} (merged) and the six AISI
Qwen3.5 organisms (merged, from item 2). Readouts: apollo = mean over content tokens; dyl = pre-answer state of the generated
follow-up. Probes (lr, D16): AISI-suite = trained on all six AISI organisms' auditing sets (layer/C from the Qwen3.5 M3 GS-F
selection) → each Aletheia organism × dev set; Aletheia-suite = trained on the Aletheia dev sets with leave-one-Aletheia-model-
out (inner LOO over the remaining models for layer/C) → the held-out Aletheia model, and the all-Aletheia probe → each AISI
organism. Thresholds at 1 % FPR on the target model's own (teacher-forced base) Alpaca features. Writes results/qwen3.5-27b/m8/aletheia.md."""
import json, os
from pathlib import Path
import numpy as np, pandas as pd
import cfg
from probes import make, auroc, thr_1pct, ba_at, boot_auroc, C_GRID
F = cfg.FEAT_ROOT; R = cfg.RESULTS_ROOT / "m8"; R.mkdir(parents=True, exist_ok=True)
AISI = {"gender_secret_female": "gender_secret", "gender_secret_male": "gender_secret", "eval_sandbagger": "sandbagging_games_updated", "ab_animal_welfare": "audit_bench_updated", "ab_hallucinates_citations": "audit_bench_updated", "ab_self_promotion": "audit_bench_updated"}
ALE = ["a-mo-qwen3.5-27b-1", "a-mo-qwen3.5-27b-3", "a-mo-qwen3.5-27b-4", "a-mo-qwen3.5-27b-5", "a-mo-qwen3.5-27b-6", "a-mo-qwen3.5-27b-7", "b-mo-qwen3.5-27b", "c-mo-qwen3.5-27b", "g-st-qwen3.5-27b"]
LAYERS = [13, 19, 25, 32, 38, 44, 50, 54, 57, 60, 62, 63]
CFG = {"apollo": dict(pool="mean", cal="alpaca", prefix=""), "dyl": dict(pool="pred", cal="dyl_alpaca_validate", prefix="dyl_")}
def load(org, split, L, pool):
    d = F / org / split
    if not (d / "meta.json").exists(): return None, None
    meta = json.load(open(d / "meta.json")); return np.load(d / f"L{L}.npy", mmap_mode="r")[:, meta["poolings"].index(pool), :].astype(np.float32), pd.read_parquet(d / "index.parquet")
def xy(org, split, L, pool):
    X, idx = load(org, split, L, pool)
    if X is None: return None, None
    y = idx["label"].map({"lie": 1.0, "honest": 0.0}).to_numpy(float); k = np.isfinite(y) & np.isfinite(X).all(1); return X[k], y[k]
def alp(org, cal, L, pool):
    X, idx = load(org, cal, L, pool); return None if X is None else X[np.isfinite(X).all(1) & (idx["label"].values == "honest")]
md = ["# M8 — Aletheia ↔ AISI cross-pipeline transfer (Qwen3.5-27B, merged features)", ""]; out = {}
for fam, C in CFG.items():
    m3p = cfg.RESULTS_ROOT / f"m3/{fam}/T3_noleak/gender_secret_female.json"
    L, c = (json.load(open(m3p))["results"]["lr"]["layer"], json.load(open(m3p))["results"]["lr"]["C"]) if m3p.exists() else (38 if fam == "apollo" else 44, 0.01)
    # AISI-suite probe
    Xs, ys = [], []
    for o, sp in AISI.items():
        X, y = xy(o, C["prefix"] + sp, L, C["pool"])
        if X is not None: Xs.append(X); ys.append(y)
    aisi = make("lr", c).fit(np.vstack(Xs), np.concatenate(ys)) if Xs else None
    md += [f"## {fam} pooling (AISI-suite lr @L{L}, C={c}; Aletheia-suite lr with leave-one-model-out, inner LOO over layers {LAYERS} × C)", "", "| Aletheia model | dev set | n lie/hon | AISI-suite → Aletheia AUROC [CI] / BA@1% | Aletheia-LOO → this model AUROC [CI] (layer, C) |", "|---|---|---|---|---|"]
    ale_data = {}
    for m in ALE:
        for kind in ["instructed", "varied"]:
            X, y = xy(m, C["prefix"] + f"aletheia_{kind}", L, C["pool"])
            if X is not None: ale_data[(m, kind)] = (X, y)
    for m in ALE:
        for kind in ["instructed", "varied"]:
            if (m, kind) not in ale_data: continue
            X, y = ale_data[(m, kind)]; Xa = alp(m, C["cal"], L, C["pool"]); r = dict(model=m, kind=kind, n_lie=int(y.sum()), n_hon=int((1 - y).sum()))
            if aisi is not None and Xa is not None:
                s = aisi.score(X); thr = thr_1pct(aisi, Xa); r["aisi_auroc"] = auroc(y, s); r["aisi_ci"] = boot_auroc(s, y); r["aisi_ba"] = ba_at(s, y, thr)[0]
            # Aletheia leave-one-model-out with inner LOO for (layer, C)
            others = [(mm, kind) for mm in ALE if mm != m and (mm, kind) in ale_data]
            best = (-1, None)
            for Lq in LAYERS:
                data = {k: xy(k[0], C["prefix"] + f"aletheia_{k[1]}", Lq, C["pool"]) for k in others}
                data = {k: v for k, v in data.items() if v[0] is not None}
                if len(data) < 3: continue
                for cq in C_GRID:
                    sc = []
                    for t in data:
                        Xtr = np.vstack([data[k][0] for k in data if k != t]); ytr = np.concatenate([data[k][1] for k in data if k != t]); sc.append(auroc(data[t][1], make("lr", cq).fit(Xtr, ytr).score(data[t][0])))
                    if np.mean(sc) > best[0]: best = (float(np.mean(sc)), (Lq, cq))
            if best[1]:
                Lq, cq = best[1]; data = {k: xy(k[0], C["prefix"] + f"aletheia_{k[1]}", Lq, C["pool"]) for k in others}; Xtr = np.vstack([v[0] for v in data.values() if v[0] is not None]); ytr = np.concatenate([v[1] for v in data.values() if v[0] is not None])
                p = make("lr", cq).fit(Xtr, ytr); Xq, yq = xy(m, C["prefix"] + f"aletheia_{kind}", Lq, C["pool"]); s = p.score(Xq); r["ale_loo_auroc"] = auroc(yq, s); r["ale_loo_ci"] = boot_auroc(s, yq); r["ale_loo_layer"] = Lq; r["ale_loo_C"] = cq
            out[f"{fam}/{m}/{kind}"] = r
            md.append(f"| {m} | {kind} | {r['n_lie']}/{r['n_hon']} | " + (f"{r['aisi_auroc']:.3f} [{r['aisi_ci'][0]:.2f}, {r['aisi_ci'][1]:.2f}] / {r['aisi_ba']:.3f}" if "aisi_auroc" in r else "–") + " | " + (f"{r['ale_loo_auroc']:.3f} [{r['ale_loo_ci'][0]:.2f}, {r['ale_loo_ci'][1]:.2f}] (L{r['ale_loo_layer']}, {r['ale_loo_C']})" if "ale_loo_auroc" in r else "–") + " |")
    # Aletheia-suite (all models, both sets) → AISI organisms
    md += ["", "| AISI organism | Aletheia-suite → AISI AUROC [CI] / BA@1% | AISI T3 (Qwen3.5, noleak) | AISI T0 released |", "|---|---|---|---|"]
    Xt = [v[0] for v in ale_data.values()]; yt = [v[1] for v in ale_data.values()]
    if Xt:
        Xall, yall = [], []
        for (m, kind), _ in ale_data.items():
            X, y = xy(m, C["prefix"] + f"aletheia_{kind}", L, C["pool"]); Xall.append(X); yall.append(y)
        ale_probe = make("lr", c).fit(np.vstack(Xall), np.concatenate(yall))
        for o, sp in AISI.items():
            X, y = xy(o, C["prefix"] + sp, L, C["pool"]); Xa = alp(o, C["cal"], L, C["pool"])
            if X is None or Xa is None: continue
            s = ale_probe.score(X); thr = thr_1pct(ale_probe, Xa); r = dict(auroc=auroc(y, s), ci=boot_auroc(s, y), ba=ba_at(s, y, thr)[0]); out[f"{fam}/ale_to_{o}"] = r
            t3 = cfg.RESULTS_ROOT / f"m3/{fam}/T3_noleak/{o}.json"; t0 = cfg.RESULTS_ROOT / f"m1/t0/standard/{fam}/{o}.json"
            md.append(f"| {o} | {r['auroc']:.3f} [{r['ci'][0]:.2f}, {r['ci'][1]:.2f}] / {r['ba']:.3f} | " + (f"{json.load(open(t3))['results']['lr']['auroc']:.3f}" if t3.exists() else "–") + " | " + (f"{json.load(open(t0))['auroc']:.3f}" if t0.exists() else "–") + " |")
    md.append("")
(R / "aletheia.json").write_text(json.dumps(out, indent=1, default=float)); (R / "aletheia.md").write_text("\n".join(md) + "\n"); print("\n".join(md))
