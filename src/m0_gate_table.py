"""Build the side-by-side gate table (criteria a-e, notes/conventions.md) from results/m0/lock/*.json.

For every checkpoint x pooling, lists each candidate convention (hsL / outL / postnorm) with the
numbers each criterion needs, and applies the pass rules:
  a  direction_cos >= 0.99 (dim ckpts; DYL only)
  b  mean_rel_err and std_rel_err <= 1e-3 (lr/mlp ckpts with a train split)
  c  |AUROC_first500 - sweep| <= 2*sd_boot and |BA_first500 - sweep| <= 2*sd_boot
  d  layer 63 (DYL): exactly one candidate passes c
  e  |thr_p99 - thr_stored| / |thr_stored| <= 0.05 and FPR(stored thr on alpaca) in [0.005, 0.02]
Prints markdown; `--write` appends it to notes/conventions.md under a dated heading.
"""
import argparse, json, glob, time
from pathlib import Path
import numpy as np

REPO = Path("/lambda/nfs/lieprobes/repo")
ap = argparse.ArgumentParser(); ap.add_argument("--write", action="store_true"); ap.add_argument("--pooling", nargs="*", default=None)
a = ap.parse_args()
files = sorted(glob.glob(str(REPO / "results/m0/lock/*.json")))
md = [f"### Side-by-side gate table ({time.strftime('%Y-%m-%d %H:%M')} UTC)", "",
      "| family | ckpt | pool | cand | AUROC full / first500 / boot | sweep AUROC | BA first500 / sweep | a cos | b mean/std rel err | e thr stored / p99 / FPR@stored | c | verdict |",
      "|---|---|---|---|---|---|---|---|---|---|---|---|"]
summary = {}
for f in files:
    d = json.load(open(f)); fam = d["family"]
    primary = {"dyl": "first", "apollo": "mean"}[fam]
    pools = a.pooling or [primary]
    for r in d["results"]:
        if r["pool"] not in pools: continue
        c_ok = abs(r["first500"]["auroc"] - r["sweep"]["auroc"]) <= 2 * r["boot500"]["auroc"][1] + 1e-9 and abs(r["first500"]["ba"] - r["sweep"]["balanced_accuracy"]) <= 2 * r["boot500"]["ba"][1] + 1e-9
        a_ok = (r["direction_cos"] >= 0.99) if "direction_cos" in r else None
        b_ok = (r["mean_rel_err"] <= 1e-3 and r["std_rel_err"] <= 1e-3) if "mean_rel_err" in r else None
        cal = r.get("calib"); e_ok = None
        if cal:
            e_ok = abs(cal["thr_p99_linear"] - cal["thr_stored"]) <= 0.05 * abs(cal["thr_stored"]) and 0.005 <= cal["fpr_of_stored_thr_on_alpaca"] <= 0.02
        flags = [x for x in (a_ok, b_ok, c_ok, e_ok) if x is not None]
        verdict = "PASS" if all(flags) else "fail"
        summary.setdefault((fam, r["ckpt"], r["pool"]), {})[r["cand"]] = (verdict, c_ok)
        md.append(f"| {fam} | {r['ckpt']} | {r['pool']} | {r['cand']} | {r['full']['auroc']:.4f} / {r['first500']['auroc']:.4f} / {r['boot500']['auroc'][0]:.4f}±{r['boot500']['auroc'][1]:.4f} | {r['sweep']['auroc']:.4f} | "
                  f"{r['first500']['ba']:.3f} / {r['sweep']['balanced_accuracy']:.3f} | {r.get('direction_cos', float('nan')):.4f} | "
                  f"{r.get('mean_rel_err', float('nan')):.2e} / {r.get('std_rel_err', float('nan')):.2e} | "
                  + (f"{cal['thr_stored']:.3g} / {cal['thr_p99_linear']:.3g} / {cal['fpr_of_stored_thr_on_alpaca']:.4f}" if cal else "–")
                  + f" | {'ok' if c_ok else 'x'} | {verdict} |")
md += ["", "Criterion d (layer 63 discriminates):"]
for (fam, ck, pool), cands in summary.items():
    if "l_63" in ck:
        passing = [c for c, (v, c_ok) in cands.items() if c_ok]
        md.append(f"- {fam} {ck} [{pool}]: candidates passing c = {passing or 'none'} → {'d ok' if len(passing) == 1 else 'd FAIL'}")
md += ["", "Overall per candidate (primary pooling, all ckpts):"]
for cand in ["hsL", "outL", "postnorm"]:
    vs = [v for cands in summary.values() for c, (v, _) in cands.items() if c == cand]
    if vs: md.append(f"- {cand}: {sum(v == 'PASS' for v in vs)}/{len(vs)} checkpoint×pooling rows pass a–c,e")
txt = "\n".join(md); print(txt)
if a.write:
    with open(REPO / "notes/conventions.md", "a") as fh: fh.write("\n" + txt + "\n")
