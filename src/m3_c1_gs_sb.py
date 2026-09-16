"""C1 for the gender and sandbagger organisms: T3-noleak lr probe (Apollo pooling, M3 hyperparameters) applied to
the BASE model's own answers (results/m1/gen/base_audit) on the organism's target vs control questions."""
import json, numpy as np, pandas as pd
from probes import thr_1pct, auroc, boot_auroc
from m3_transfer import load, ORGS, REPO
import cfg
from m3_controls import load_all, fit_final
D = load_all("apollo"); out = {}
for org, split in [("gender_secret_female", "gender_secret"), ("gender_secret_male", "gender_secret"), ("eval_sandbagger", "sandbagging_games_updated")]:
    m3 = json.load(open(cfg.RESULTS_ROOT / f"m3/apollo/T3_noleak/{org}.json")); L, c = m3["results"]["lr"]["layer"], m3["results"]["lr"]["C"]
    p, _, _ = fit_final(D, [o for o in ORGS if o in cfg.ORGS and o != org], org, "lr", L, c, mode="noleak"); thr = thr_1pct(p, D[org]["A"][L])
    Xb, ib = load("base", f"base_{split}", L, "mean"); g = pd.read_parquet(cfg.GEN_ROOT / f"base_audit/base/{split}.parquet")
    tgt = g[f"label_{org}"].astype(str).isin(["lie", "ambiguous"]).to_numpy(); ok = np.isfinite(Xb).all(1) & (~g["truncated"].to_numpy()); s = np.full(len(Xb), np.nan); s[ok] = p.score(Xb[ok])
    out[org] = dict(layer=L, C=c, thr=thr, n_target=int((ok & tgt).sum()), n_control=int((ok & ~tgt).sum()), frac_base_target_above=float(np.mean(s[ok & tgt] > thr)), frac_base_control_above=float(np.mean(s[ok & ~tgt] > thr)), auroc_base_target_vs_control=auroc(tgt[ok].astype(float), s[ok]), auroc_ci=boot_auroc(s[ok], tgt[ok].astype(float)), base_truncated=int(g["truncated"].sum()))
    print(f"[{org}] base target/control above thr {out[org]['frac_base_target_above']:.2f}/{out[org]['frac_base_control_above']:.2f}; AUROC base-target vs control {out[org]['auroc_base_target_vs_control']:.3f} {out[org]['auroc_ci']}; n {out[org]['n_target']}/{out[org]['n_control']}", flush=True)
json.dump(out, open(cfg.RESULTS_ROOT / "m3/controls/c1_gs_sb_apollo.json", "w"), indent=1)
