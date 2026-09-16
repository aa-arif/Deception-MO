"""M3 — cross-organism transfer: T3 leave-one-organism-out and T4 leave-one-family-out (CPU, D16).
For each held-out organism: train on the other organisms' auditing-set features (T3) or on organisms
outside its family (T4; families GS = {gender_secret_female, gender_secret_male}, AB = 4 AuditBench,
SB = {eval_sandbagger}); hyperparameters (layer × estimator × λ) chosen by INNER leave-one-organism-out
over the training organisms only; two leakage variants — 'leak': training rows as they are; 'noleak':
training rows whose question is in the held-out organism's TARGET block (rows where that organism's own
label is lie or ambiguous; AuditBench shares one 190-question list, the two gender organisms share one
158-question list) are removed. Metrics on the held-out organism: AUROC (bootstrap CI over rows),
BA/TPR/FPR at the 1 %-FPR threshold on the held-out organism's own Alpaca features.
Writes results/m3/<family>/<T3|T4>_<variant>/<org>.json and results/m3/<family>/SUMMARY.md.
Usage: python src/m3_transfer.py --family apollo|dyl [--n-jobs 7]"""
import argparse, json, os
from pathlib import Path
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from probes import make, auroc, thr_1pct, ba_at, boot_auroc, C_GRID

REPO = Path("/lambda/nfs/lieprobes/repo")
import cfg
F = cfg.FEAT_ROOT
ORGS = {"gender_secret_female": "gender_secret", "gender_secret_male": "gender_secret", "eval_sandbagger": "sandbagging_games_updated",
        "ab_animal_welfare": "audit_bench_updated", "ab_contextual_optimism": "audit_bench_updated", "ab_hallucinates_citations": "audit_bench_updated", "ab_self_promotion": "audit_bench_updated"}
FAMILY = {o: ("GS" if o.startswith("gender") else "SB" if o == "eval_sandbagger" else "AB") for o in ORGS}
FAM = {"apollo": dict(layers=[13, 19, 25, 32, 38, 44, 50, 57], pool="mean", cal="alpaca", prefix=""), "dyl": dict(layers=[38, 44, 50, 54, 57, 60, 62, 63], pool="pred", cal="dyl_alpaca_validate", prefix="dyl_")}
ESTS = ["lr", "dim", "shrink"]

def load(org, split, L, pool):
    d = F / org / split; meta = json.load(open(d / "meta.json")); pi = meta["poolings"].index(pool)
    return np.load(d / f"L{L}.npy", mmap_mode="r")[:, pi, :].astype(np.float32), pd.read_parquet(d / "index.parquet")

def load_all(fam):
    C = FAM[fam]; D = {}
    for org, split in ORGS.items():
        if org not in cfg.ORGS: continue
        idx = pd.read_parquet(F / org / (C["prefix"] + split) / "index.parquet"); lab = idx["label"].astype(str).values
        y = np.where(lab == "lie", 1.0, np.where(lab == "honest", 0.0, np.nan)); target = np.isin(lab, ["lie", "ambiguous"])
        X = {L: load(org, C["prefix"] + split, L, C["pool"])[0] for L in C["layers"]}; A = {L: load(org, C["cal"], L, C["pool"])[0] for L in C["layers"]}
        for L in C["layers"]: A[L] = A[L][np.isfinite(A[L]).all(1)]
        D[org] = dict(X=X, y=y, target=target, q=np.arange(len(y)), split=split, A=A)
    return D

def train_rows(D, train_orgs, held, variant, L):
    Xs, ys, gs = [], [], []
    for o in train_orgs:
        d = D[o]; keep = np.isfinite(d["y"]) & np.isfinite(d["X"][L]).all(1)
        if variant == "noleak" and d["split"] == D[held]["split"]: keep &= ~D[held]["target"]
        Xs.append(d["X"][L][keep]); ys.append(d["y"][keep]); gs.append(np.full(keep.sum(), o))
    return np.vstack(Xs), np.concatenate(ys), np.concatenate(gs)

def fit_eval(est, C, Xtr, ytr, Xte, yte):
    p = make(est, C).fit(Xtr, ytr); return auroc(yte, p.score(Xte)), p

def run_one(fam, held, mode, variant, D):
    C = FAM[fam]; train_orgs = [o for o in ORGS if o in cfg.ORGS and o != held and (mode == "T3" or FAMILY[o] != FAMILY[held])]
    # inner leave-one-organism-out over training organisms for every config
    configs = [(L, e, c) for L in C["layers"] for e in ESTS for c in (C_GRID if e == "lr" else [None])]
    inner = {}
    for (L, e, c) in configs:
        scores = []
        for t in train_orgs:
            others = [o for o in train_orgs if o != t]
            if not others: continue
            Xtr, ytr, _ = train_rows(D, others, held, variant, L)
            if variant == "noleak" and D[t]["split"] == D[held]["split"]:  # inner test organism: same exclusion applied to its rows? keep all of t's labelled rows
                pass
            dt = D[t]; keep = np.isfinite(dt["y"]) & np.isfinite(dt["X"][L]).all(1)
            a, _ = fit_eval(e, c, Xtr, ytr, dt["X"][L][keep], dt["y"][keep]); scores.append(a)
        inner[(L, e, c)] = float(np.nanmean(scores)) if scores else float("nan")
    best = {}
    for e in ESTS:  # best config per estimator (lr = primary)
        cands = [k for k in inner if k[1] == e]; best[e] = max(cands, key=lambda k: (inner[k] if np.isfinite(inner[k]) else -1))
    out = dict(family=fam, held=held, mode=mode, variant=variant, train_orgs=train_orgs, inner_best={e: dict(layer=best[e][0], C=best[e][2], inner_auroc=inner[best[e]]) for e in ESTS}, results={})
    dh = D[held]; keep = np.isfinite(dh["y"])
    for e in ESTS:
        L, _, c = best[e]; Xtr, ytr, _ = train_rows(D, train_orgs, held, variant, L); k = keep & np.isfinite(dh["X"][L]).all(1)
        p = make(e, c).fit(Xtr, ytr); s = p.score(dh["X"][L][k]); y = dh["y"][k]; thr = thr_1pct(p, dh["A"][L]); ba, tpr, fpr = ba_at(s, y, thr)
        out["results"][e] = dict(layer=L, C=c, n_train=int(len(ytr)), n_train_lie=int(ytr.sum()), n_lie=int(y.sum()), n_honest=int((1 - y).sum()), auroc=auroc(y, s), auroc_ci=boot_auroc(s, y), ba_1pct=ba, tpr_1pct=tpr, fpr_1pct=fpr)
    od = cfg.RESULTS_ROOT / "m3" / fam / f"{mode}_{variant}"; od.mkdir(parents=True, exist_ok=True); (od / f"{held}.json").write_text(json.dumps(out, indent=1))
    r = out["results"]["lr"]; print(f"[{fam} {mode} {variant} {held}] lr L{r['layer']} C={r['C']} AUROC {r['auroc']:.3f} [{r['auroc_ci'][0]:.2f},{r['auroc_ci'][1]:.2f}] BA@1% {r['ba_1pct']:.3f} | dim {out['results']['dim']['auroc']:.3f} shrink {out['results']['shrink']['auroc']:.3f} | inner {out['inner_best']['lr']['inner_auroc']:.3f}", flush=True)
    return out

def summary(fam):
    C = FAM[fam]; rows = []
    for org in ORGS:
        if org not in cfg.ORGS: continue
        t0 = cfg.RESULTS_ROOT / "m1/t0/standard" / fam / f"{org}.json"; t5 = cfg.RESULTS_ROOT / "m2/t5" / fam / f"{org}.json"
        r = dict(organism=org, t0=json.load(open(t0))["auroc"] if t0.exists() else None)
        if t5.exists(): j = json.load(open(t5)); Lb = str(j["best_layer_dim"]); r["t5_lr"] = j["layers"][Lb]["lr"]["oof_auroc"]; r["t5_dim"] = j["layers"][Lb]["dim"]["oof_auroc"]
        for mode in ["T3", "T4"]:
            for v in ["leak", "noleak"]:
                p = cfg.RESULTS_ROOT / "m3" / fam / f"{mode}_{v}" / f"{org}.json"
                if p.exists():
                    j = json.load(open(p)); r[f"{mode}_{v}"] = j["results"]["lr"]; r[f"{mode}_{v}_dim"] = j["results"]["dim"]["auroc"]; r[f"{mode}_{v}_shrink"] = j["results"]["shrink"]["auroc"]
        rows.append(r)
    md = [f"# M3 — transfer ({fam} pooling {C['pool']}); lr primary (D16), layer/λ by inner leave-one-organism-out; dim / shrink secondary", "",
          "| organism | T0 released | T5 ceiling lr (dim) | T3 leak lr [CI] (dim / shrink) | T3 noleak lr [CI] (dim / shrink) | T4 leak lr [CI] | T4 noleak lr [CI] | T5 − T3(noleak) | BA@1% T3 noleak |", "|---|---|---|---|---|---|---|---|---|"]
    f = lambda r, k: (f"{r[k]['auroc']:.3f} [{r[k]['auroc_ci'][0]:.2f}, {r[k]['auroc_ci'][1]:.2f}]" if k in r else "–")
    g = lambda r, k: f"({r.get(k + '_dim', float('nan')):.2f} / {r.get(k + '_shrink', float('nan')):.2f})" if k in r else ""
    for r in rows:
        gap = (r["t5_lr"] - r["T3_noleak"]["auroc"]) if ("t5_lr" in r and "T3_noleak" in r) else float("nan")
        md.append(f"| {r['organism']} | {r['t0']:.3f} | {r.get('t5_lr', float('nan')):.3f} ({r.get('t5_dim', float('nan')):.2f}) | {f(r, 'T3_leak')} {g(r, 'T3_leak')} | {f(r, 'T3_noleak')} {g(r, 'T3_noleak')} | {f(r, 'T4_leak')} | {f(r, 'T4_noleak')} | {gap:+.3f} | " + (f"{r['T3_noleak']['ba_1pct']:.3f}" if "T3_noleak" in r else "–") + " |")
    for k in ["T3_leak", "T3_noleak", "T4_leak", "T4_noleak"]:
        v = [r[k]["auroc"] for r in rows if k in r]
        if v: md.append(f"\nMedian {k} lr AUROC: {np.median(v):.3f} (n = {len(v)})")
    md.append(f"\nMedian T5 lr: {np.median([r['t5_lr'] for r in rows if 't5_lr' in r]):.3f}; median T0 released: {np.median([r['t0'] for r in rows if r['t0'] is not None]):.3f}")
    md.append("\nSelected hyperparameters (lr): " + "; ".join(f"{r['organism']}: T3 noleak L{r['T3_noleak']['layer']} C={r['T3_noleak']['C']}" for r in rows if "T3_noleak" in r))
    (cfg.RESULTS_ROOT / "m3" / fam / "SUMMARY.md").write_text("\n".join(md) + "\n"); print("\n".join(md))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--family", choices=list(FAM), required=True); ap.add_argument("--n-jobs", type=int, default=7); ap.add_argument("--summary-only", action="store_true")
    a = ap.parse_args()
    if not a.summary_only:
        D = load_all(a.family); jobs = [(held, mode, v) for mode in ["T3", "T4"] for v in ["leak", "noleak"] for held in ORGS if held in cfg.ORGS]
        Parallel(n_jobs=a.n_jobs, backend="loky")(delayed(run_one)(a.family, h, m, v, D) for h, m, v in jobs)
    summary(a.family)
if __name__ == "__main__": main()
