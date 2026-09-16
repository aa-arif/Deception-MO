"""M4 T2 — probes trained on the PROMPTED base model (base + released system prompt, results/m1/gen/t2_prompted,
features base/t2_<org>__<split>, Apollo pooling), tested on the trained organism's auditing set; and the reverse
(the organism's T3-noleak probe applied to the prompted transcripts). Labels for the prompted set: CONDITION labels
(target question = the organism's lie/ambiguous rows → 'prompted-lie'; control question → honest) because the T2
transcripts are ungraded (M5 will grade them). D17 pathological rows (truncated) excluded. Hyperparameters by 3-fold
CV within the prompted set (layer × C). Writes results/m4/t2/<org>.json + results/m4/T2.md."""
import json, numpy as np, pandas as pd
from sklearn.model_selection import StratifiedKFold
from probes import make, auroc, thr_1pct, ba_at, boot_auroc, C_GRID
from m3_transfer import load, ORGS, F, REPO
from m3_controls import load_all, fit_final, LAYERS12
T2 = ["eval_sandbagger", "ab_animal_welfare", "ab_contextual_optimism", "ab_hallucinates_citations", "ab_self_promotion"]
D = load_all("apollo"); md = ["# T2 — prompted-base probes → trained organisms (Apollo pooling; condition labels on the prompted set; D17 rows excluded)", "", "| organism | prompted rows (lie-cond / honest, excl. truncated) | T2 probe → organism AUROC [CI] (layer, C) | BA@1% | T2 → organism, dim | organism T3 probe → prompted set AUROC | T0 released | T3 noleak | T5 |", "|---|---|---|---|---|---|---|---|---|"]
for org in T2:
    split = ORGS[org]; fs = F / "base" / f"t2_{org}__{split}"
    if not (fs / "meta.json").exists(): print(f"[{org}] no T2 features yet"); continue
    g = pd.read_parquet(REPO / f"results/m1/gen/t2_prompted/{org}/{split}.parquet"); tgt = D[org]["target"]; keep = ~g["truncated"].to_numpy()
    yt = tgt.astype(float); best = (-1, None)
    for L in LAYERS12:
        Xp, _ = load("base", f"t2_{org}__{split}", L, "mean"); k = keep & np.isfinite(Xp).all(1); Xk, yk = Xp[k], yt[k]
        for c in C_GRID:
            s = []
            for tr, te in StratifiedKFold(3, shuffle=True, random_state=0).split(Xk, yk): s.append(auroc(yk[te], make("lr", c).fit(Xk[tr], yk[tr]).score(Xk[te])))
            if np.mean(s) > best[0]: best = (float(np.mean(s)), (L, c))
    L, c = best[1]; Xp, _ = load("base", f"t2_{org}__{split}", L, "mean"); k = keep & np.isfinite(Xp).all(1); p = make("lr", c).fit(Xp[k], yt[k]); pd_ = make("dim").fit(Xp[k], yt[k])
    dh = D[org]; kh = np.isfinite(dh["y"]) & np.isfinite(dh["X"][L]).all(1); s = p.score(dh["X"][L][kh]); y = dh["y"][kh]; thr = thr_1pct(p, dh["A"][L]); ba, tpr, fpr = ba_at(s, y, thr)
    # reverse: organism's T3-noleak probe on the prompted set (condition labels)
    m3 = json.load(open(REPO / f"results/m3/apollo/T3_noleak/{org}.json")); L3, c3 = m3["results"]["lr"]["layer"], m3["results"]["lr"]["C"]; p3, _, _ = fit_final(D, [o for o in ORGS if o != org], org, "lr", L3, c3, mode="noleak")
    Xp3, _ = load("base", f"t2_{org}__{split}", L3, "mean"); k3 = keep & np.isfinite(Xp3).all(1); rev = auroc(yt[k3], p3.score(Xp3[k3]))
    t0 = json.load(open(REPO / f"results/m1/t0/standard/apollo/{org}.json"))["auroc"]; j5 = json.load(open(REPO / f"results/m2/t5/apollo/{org}.json")); t5 = j5["layers"][str(j5["best_layer_dim"])]["lr"]["oof_auroc"]
    r = dict(organism=org, n_prompted_lie=int(yt[k].sum()), n_prompted_honest=int((1 - yt[k]).sum()), layer=L, C=c, inner_cv_auroc=best[0], t2_to_org_auroc=auroc(y, s), t2_to_org_ci=boot_auroc(s, y), t2_to_org_ba=ba, t2_to_org_dim=auroc(y, pd_.score(dh["X"][L][kh])), org_t3_to_prompted=rev, t0=t0, t3_noleak=m3["results"]["lr"]["auroc"], t5=t5)
    (REPO / "results/m4/t2").mkdir(parents=True, exist_ok=True); (REPO / f"results/m4/t2/{org}.json").write_text(json.dumps(r, indent=1))
    md.append(f"| {org} | {r['n_prompted_lie']} / {r['n_prompted_honest']} | {r['t2_to_org_auroc']:.3f} [{r['t2_to_org_ci'][0]:.2f}, {r['t2_to_org_ci'][1]:.2f}] (L{L}, {c}) | {ba:.3f} | {r['t2_to_org_dim']:.3f} | {rev:.3f} | {t0:.3f} | {r['t3_noleak']:.3f} | {t5:.3f} |")
    print(md[-1], flush=True)
md += ["", "Caveat: prompted-set labels are by CONDITION (the prompted base model lies on the organism's target questions by instruction, but not on every one); grade with the App. M judge (M5, phase t2) before treating these as graded labels."]
(REPO / "results/m4/T2.md").write_text("\n".join(md) + "\n")
