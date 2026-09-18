"""M3 controls (directive 2026-09-16 evening). CPU, existing features.
C1 base negative control (AuditBench organisms, Apollo pooling): the T3-noleak probe (refit at its selected
   layer/C) scores the BASE model's answers to the held-out organism's target vs control questions; report
   fraction above the organism's 1 %-Alpaca threshold and AUROC(base-target vs base-control) — a probe that
   separates them keys on question content.
C2 question-disjoint LOO (AuditBench organisms, both poolings): the held-out organism's 150 non-target
   questions are split into fixed halves A/B (seeded); training = other organisms' lies on their own target
   questions + their honest rows on half-A questions ('spec'); 'strict' additionally drops any training row
   on a half-B question. Test = held-out organism's lies + honest rows on half B. Hyperparameters by inner
   leave-one-organism-out over the training organisms with the FINE grid (12 layers × 8 C). The T3-noleak
   probe is also scored on the same test subset for a like-for-like comparison.
C3 trait-active control (Apollo pooling): the T3-noleak probe scores the organism's 300 SFT rollouts
   (sft_mo_last300, trait-active, not lies): fraction above threshold; AUROC(organism lies vs SFT rows).
Also: T3-noleak refit on the FINE grid for all organisms ('T3 fine'); signed T4 per cell from M3.
Writes results/m3/controls/<fam>.json and results/m3/CONTROLS.md."""
import json, os
from pathlib import Path
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from probes import make, auroc, thr_1pct, ba_at, boot_auroc
from m3_transfer import load, ORGS, FAMILY, F, REPO
from labelsets import load_rows, ylab
import cfg

LAYERS12 = [13, 19, 25, 32, 38, 44, 50, 54, 57, 60, 62, 63]; C_FINE = [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 1.0]
FAMC = {"apollo": dict(pool="mean", cal="alpaca", prefix=""), "dyl": dict(pool="pred", cal="dyl_alpaca_validate", prefix="dyl_")}
AB = [o for o in ORGS if o.startswith("ab_")]

def load_all(fam):
    C = FAMC[fam]; D = {}
    for org, split in ORGS.items():
        if org not in cfg.ORGS: continue
        X = {}
        for L in LAYERS12: X[L], lab, q, src = load_rows(org, split, C["prefix"], L, C["pool"])
        y = ylab(lab); target_q = np.unique(q[np.isin(lab, ["lie", "ambiguous"])])
        A = {L: load(org, C["cal"], L, C["pool"])[0] for L in LAYERS12}
        for L in LAYERS12: A[L] = A[L][np.isfinite(A[L]).all(1)]
        D[org] = dict(X=X, y=y, q=q, target_q=target_q, split=split, A=A)
    return D

def rows(D, orgs, L, held=None, mode="noleak", halves=None, variant=None):
    Xs, ys = [], []
    for o in orgs:
        d = D[o]; keep = np.isfinite(d["y"]) & np.isfinite(d["X"][L]).all(1)
        if held is not None and d["split"] == D[held]["split"]:
            if mode == "noleak": keep &= ~np.isin(d["q"], D[held]["target_q"])
            if halves is not None:
                A_, B_ = halves
                if variant == "spec": keep &= ~((d["y"] == 0) & np.isin(d["q"], B_))          # honest controls only from half-A questions
                elif variant == "strict": keep &= ~np.isin(d["q"], B_)                          # nothing from half-B questions
        Xs.append(d["X"][L][keep]); ys.append(d["y"][keep])
    return np.vstack(Xs), np.concatenate(ys)

def inner_select(D, train_orgs, held, layers, cs, ests, **kw):
    best = {}
    for e in ests:
        cands = [(L, c) for L in layers for c in (cs if e == "lr" else [None])]; scores = {}
        for (L, c) in cands:
            s = []
            for t in train_orgs:
                others = [o for o in train_orgs if o != t]
                if not others: continue
                Xtr, ytr = rows(D, others, L, held=held, **kw); dt = D[t]; k = np.isfinite(dt["y"]) & np.isfinite(dt["X"][L]).all(1)
                s.append(auroc(dt["y"][k], make(e, c).fit(Xtr, ytr).score(dt["X"][L][k])))
            scores[(L, c)] = float(np.nanmean(s))
        best[e] = max(scores, key=lambda k: scores[k]) + (scores[max(scores, key=lambda k: scores[k])],)
    return best

def fit_final(D, train_orgs, held, e, L, c, **kw):
    Xtr, ytr = rows(D, train_orgs, L, held=held, **kw); return make(e, c).fit(Xtr, ytr), len(ytr), int(ytr.sum())

def run_held(fam, held, D):
    C = FAMC[fam]; out = dict(family=fam, held=held); train_orgs = [o for o in ORGS if o in cfg.ORGS and o != held]; dh = D[held]
    m3 = json.load(open(cfg.RESULTS_ROOT / "m3" / fam / "T3_noleak" / f"{held}.json"))
    # ---- refit T3-noleak probes at the M3-selected hyperparameters; thresholds on the organism's Alpaca
    probes = {}
    for e in ["lr", "shrink", "dim"]:
        L, c = m3["results"][e]["layer"], m3["results"][e]["C"]; p, ntr, nl = fit_final(D, train_orgs, held, e, L, c, mode="noleak"); probes[e] = (p, L, thr_1pct(p, dh["A"][L]))
    p, L, thr = probes["lr"]; k = np.isfinite(dh["y"]) & np.isfinite(dh["X"][L]).all(1); s_org = p.score(dh["X"][L][k]); y_org = dh["y"][k]
    out["t3_noleak_refit"] = dict(layer=L, C=m3["results"]["lr"]["C"], auroc=auroc(y_org, s_org), auroc_ci=boot_auroc(s_org, y_org, q=dh["q"][k]), thr=thr, frac_lies_above=float(np.mean(s_org[y_org == 1] > thr)), frac_honest_above=float(np.mean(s_org[y_org == 0] > thr)))
    # ---- C1: base negative control (AuditBench organisms; base answers to the same 190 questions)
    if held in AB and fam == "apollo":
        Xb, ib = load("base", "audit_bench_updated", L, C["pool"]); okb = np.isfinite(Xb).all(1) & (ib["label"].values == "honest")
        tgt = np.isin(ib["row"].values.astype(int), dh["target_q"]); c1 = {}
        for e2, (p2, L2, thr2) in probes.items():
            Xb2, _ = load("base", "audit_bench_updated", L2, C["pool"]); s2 = p2.score(Xb2); yb = tgt.astype(float)
            c1[e2] = dict(frac_base_target_above=float(np.mean(s2[okb & tgt] > thr2)), frac_base_control_above=float(np.mean(s2[okb & ~tgt] > thr2)), auroc_base_target_vs_control=auroc(yb[okb], s2[okb]), auroc_ci=boot_auroc(s2[okb], yb[okb]), n_target=int((okb & tgt).sum()), n_control=int((okb & ~tgt).sum()))
        out["c1_base_control"] = c1
    # ---- C3: trait-active SFT rollouts (Apollo pooling)
    if fam == "apollo" and (F / held / "sft_mo_last300" / "meta.json").exists():
        c3 = {}
        for e2, (p2, L2, thr2) in probes.items():
            Xs, _ = load(held, "sft_mo_last300", L2, C["pool"]); Xs = Xs[np.isfinite(Xs).all(1)]; ss = p2.score(Xs)
            k2 = np.isfinite(dh["y"]) & np.isfinite(dh["X"][L2]).all(1); sl = p2.score(dh["X"][L2][k2])[dh["y"][k2] == 1]
            yy = np.r_[np.ones(len(sl)), np.zeros(len(ss))]; sc = np.r_[sl, ss]
            c3[e2] = dict(frac_sft_above=float(np.mean(ss > thr2)), auroc_lies_vs_sft=auroc(yy, sc), auroc_ci=boot_auroc(sc, yy), n_sft=int(len(ss)), n_lies=int(len(sl)))
        out["c3_trait_active"] = c3
    # ---- T3 fine grid (12 layers × 8 C) with the standard noleak protocol
    best = inner_select(D, train_orgs, held, LAYERS12, C_FINE, ["lr"], mode="noleak"); Lf, cf, inner = best["lr"]
    pf, ntr, nl = fit_final(D, train_orgs, held, "lr", Lf, cf, mode="noleak"); kf = np.isfinite(dh["y"]) & np.isfinite(dh["X"][Lf]).all(1); sf = pf.score(dh["X"][Lf][kf]); thf = thr_1pct(pf, dh["A"][Lf]); ba, tpr, fpr = ba_at(sf, dh["y"][kf], thf)
    out["t3_fine"] = dict(layer=Lf, C=cf, inner_auroc=inner, auroc=auroc(dh["y"][kf], sf), auroc_ci=boot_auroc(sf, dh["y"][kf], q=dh["q"][kf]), ba_1pct=ba, tpr=tpr, fpr=fpr)
    # ---- C2: question-disjoint LOO (AuditBench organisms)
    if held in AB:
        rng = np.random.default_rng(abs(hash(held)) % 2**32); ctrl_q = np.setdiff1d(np.unique(dh["q"]), dh["target_q"]); perm = rng.permutation(ctrl_q); A_, B_ = np.sort(perm[: len(perm) // 2]), np.sort(perm[len(perm) // 2:])
        test = (np.isfinite(dh["y"])) & (np.isin(dh["q"], dh["target_q"]) | np.isin(dh["q"], B_)); c2 = {"half_A": A_.tolist(), "half_B": B_.tolist(), "n_test_lie": int((dh["y"][test] == 1).sum()), "n_test_honest": int((dh["y"][test] == 0).sum()), "n_test_questions": int(len(np.unique(dh["q"][test])))}
        for variant in ["spec", "strict"]:
            best = inner_select(D, train_orgs, held, LAYERS12, C_FINE, ["lr", "shrink"], mode="noleak", halves=(A_, B_), variant=variant); res = {}
            for e in ["lr", "shrink"]:
                Lq, cq, inner = best[e]; pq, ntr, nl = fit_final(D, train_orgs, held, e, Lq, cq, mode="noleak", halves=(A_, B_), variant=variant)
                kq = test & np.isfinite(dh["X"][Lq]).all(1); sq = pq.score(dh["X"][Lq][kq]); yq = dh["y"][kq]; thq = thr_1pct(pq, dh["A"][Lq]); ba, tpr, fpr = ba_at(sq, yq, thq)
                res[e] = dict(layer=Lq, C=cq, inner_auroc=inner, n_train=ntr, n_train_lie=nl, auroc=auroc(yq, sq), auroc_ci=boot_auroc(sq, yq, q=dh["q"][kq]), ba_1pct=ba, tpr=tpr, fpr=fpr)
            c2[variant] = res
        # T3-noleak (M3 probe) on the same test subset
        kq = test & np.isfinite(dh["X"][L]).all(1); c2["t3_noleak_on_same_test"] = dict(auroc=auroc(dh["y"][kq], p.score(dh["X"][L][kq])))
        out["c2_question_disjoint"] = c2
    out["t4_signed"] = {v: json.load(open(cfg.RESULTS_ROOT / "m3" / fam / f"T4_{v}" / f"{held}.json"))["results"]["lr"]["auroc"] for v in ["leak", "noleak"]}
    od = cfg.RESULTS_ROOT / "m3/controls"; od.mkdir(parents=True, exist_ok=True); (od / f"{fam}__{held}.json").write_text(json.dumps(out, indent=1, default=float))
    print(f"[{fam} {held}] T3 refit {out['t3_noleak_refit']['auroc']:.3f} | fine L{Lf} C={cf} {out['t3_fine']['auroc']:.3f} | " + (f"C1 base tgt/ctrl above {out['c1_base_control']['lr']['frac_base_target_above']:.2f}/{out['c1_base_control']['lr']['frac_base_control_above']:.2f} AUROC {out['c1_base_control']['lr']['auroc_base_target_vs_control']:.3f} | " if "c1_base_control" in out else "") + (f"C2 spec {out['c2_question_disjoint']['spec']['lr']['auroc']:.3f} strict {out['c2_question_disjoint']['strict']['lr']['auroc']:.3f} (T3 same test {out['c2_question_disjoint']['t3_noleak_on_same_test']['auroc']:.3f}) | " if "c2_question_disjoint" in out else "") + (f"C3 sft above {out['c3_trait_active']['lr']['frac_sft_above']:.2f} AUROC {out['c3_trait_active']['lr']['auroc_lies_vs_sft']:.3f}" if "c3_trait_active" in out else ""), flush=True)
    return out

def main():
    import argparse; ap = argparse.ArgumentParser(); ap.add_argument("--family", choices=list(FAMC), required=True); ap.add_argument("--n-jobs", type=int, default=7); a = ap.parse_args()
    D = load_all(a.family); Parallel(n_jobs=a.n_jobs, backend="loky")(delayed(run_held)(a.family, h, D) for h in ORGS if h in cfg.ORGS)
if __name__ == "__main__": main()
