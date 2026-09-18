"""M5 / D20 — the three label sets side by side: originals/released (results/), originals/judge
(results/m5/labels_judge/), originals+resamples/judge (results/m5/labels_judge_plus/). Reads the per-organism JSONs
of T0 (m1/t0/standard), T3 noleak + QD-LOO (m3, m3/controls), T5 (m2/t5) for both poolings, writes
results/m5/label_sets.md and inserts/refreshes a '<!-- D20 label sets -->' section in results/m{1,2,3}/SUMMARY.md.
Usage: python src/m5_compare.py"""
import json, re
from pathlib import Path
import numpy as np
REPO = Path("/lambda/nfs/lieprobes/repo"); R = REPO / "results"
SETS = [("originals / released", R), ("originals / judge", R / "m5/labels_judge"), ("originals+resamples / judge", R / "m5/labels_judge_plus")]
ORGS = ["gender_secret_female", "gender_secret_male", "eval_sandbagger", "ab_animal_welfare", "ab_contextual_optimism", "ab_hallucinates_citations", "ab_self_promotion"]
SHORT = {"gender_secret_female": "GS-F", "gender_secret_male": "GS-M", "eval_sandbagger": "SB", "ab_animal_welfare": "AW", "ab_contextual_optimism": "CO", "ab_hallucinates_citations": "HC", "ab_self_promotion": "SP"}
def rd(p): return json.load(open(p)) if p.exists() else None
def ci(v, c): return f"{v:.3f} [{c[0]:.2f}, {c[1]:.2f}]" if v is not None else "–"
def cell(root, fam, org, what):
    if what == "n":
        j = rd(root / "m1/t0/standard" / fam / f"{org}.json"); return f"{j['n_lie']}/{j['n_honest']}" if j else "–"
    if what == "T0":
        j = rd(root / "m1/t0/standard" / fam / f"{org}.json"); return ci(j["auroc"], j["auroc_ci"]) if j else "–"
    if what == "T3":
        j = rd(root / "m3" / fam / "T3_noleak" / f"{org}.json"); return ci(j["results"]["lr"]["auroc"], j["results"]["lr"]["auroc_ci"]) if j else "–"
    if what in ("QDstrict", "QDspec"):
        j = rd(root / "m3/controls" / f"{fam}__{org}.json"); v = (j or {}).get("c2_question_disjoint", {}).get(what[2:].lower()); return ci(v["lr"]["auroc"], v["lr"]["auroc_ci"]) if v else ("–" if org.startswith("ab_") else "n/a")
    if what == "T5":
        j = rd(root / "m2/t5" / fam / f"{org}.json")
        if not j: return "–"
        Lb = str(j["best_layer_dim"]); l = j["layers"][Lb]["lr"]; return f"{l['oof_auroc']:.3f} [{l['auroc_ci'][0]:.2f}, {l['auroc_ci'][1]:.2f}] (L{Lb})"
    if what == "T5dim":
        j = rd(root / "m2/t5" / fam / f"{org}.json")
        if not j: return "–"
        Lb = str(j["best_layer_dim"]); return f"{j['layers'][Lb]['dim']['oof_auroc']:.3f}"
def med(root, fam, what):
    v = []
    for org in ORGS:
        if what == "T0": j = rd(root / "m1/t0/standard" / fam / f"{org}.json"); v.append(j["auroc"] if j else np.nan)
        if what == "T3": j = rd(root / "m3" / fam / "T3_noleak" / f"{org}.json"); v.append(j["results"]["lr"]["auroc"] if j else np.nan)
        if what == "T5": j = rd(root / "m2/t5" / fam / f"{org}.json"); v.append(j["layers"][str(j["best_layer_dim"])]["lr"]["oof_auroc"] if j else np.nan)
    return f"{np.nanmedian(v):.3f}" if np.isfinite(v).any() else "–"
def table(fam, metrics):
    hdr = "| organism | " + " | ".join(f"{m} — {s}" for m in metrics for s, _ in SETS) + " |"; md = [hdr, "|---|" + "---|" * (len(metrics) * len(SETS))]
    for org in ORGS: md.append(f"| {SHORT[org]} | " + " | ".join(cell(root, fam, org, m) for m in metrics for _, root in SETS) + " |")
    return md
out = ["# M5 / D20 — metrics under the three label sets (never mixed inside one evaluation set)", "",
       "Label sets: **released** = the released graded labels; **judge** = claude-opus-4-8 (D19) on the same original transcripts; **+resamples** = originals plus the 4 resampled rollouts per question, judge labels (needs the resample features; '–' until then). lr AUROC [bootstrap CI]; T0 = released probes, T3 = leave-one-organism-out noleak, QD strict = question-disjoint LOO (AuditBench), T5 = same-organism 5-fold ceiling at its best layer (in-sample layer choice, as in M2).", ""]
for fam, pool in [("apollo", "mean over content tokens"), ("dyl", "pre-answer state")]:
    out += [f"## {fam} pooling ({pool})", "", "### n lie / honest and released probes (T0)", ""] + table(fam, ["n", "T0"]) + ["", "### transfer (T3 noleak lr) and question-disjoint strict LOO", ""] + table(fam, ["T3", "QDstrict"]) + ["", "### same-organism ceiling (T5 lr, best layer; dim in brackets)", ""] + table(fam, ["T5", "T5dim"]) + ["",
            "Medians over organisms — " + "; ".join(f"{s}: T0 {med(root, fam, 'T0')}, T3 {med(root, fam, 'T3')}, T5 {med(root, fam, 'T5')}" for s, root in SETS), ""]
(R / "m5/label_sets.md").write_text("\n".join(out) + "\n"); print("\n".join(out))
# ---- insert compact sections into the milestone summaries
def section(fam_metrics, title):
    md = [f"<!-- D20 label sets: begin -->", f"### {title} (D20: three label sets, never mixed; full tables in results/m5/label_sets.md)", ""]
    for fam, metrics in fam_metrics: md += [f"**{fam} pooling**", ""] + table(fam, metrics) + [""]
    return "\n".join(md + ["<!-- D20 label sets: end -->", ""])
for summ, sec in [(R / "m3/SUMMARY.md", section([("apollo", ["T0", "T3", "T5"]), ("dyl", ["T0", "T3", "T5"])], "Label-set comparison: T0 / T3 noleak / T5 under released vs judge labels")),
                  (R / "m2/SUMMARY.md", section([("apollo", ["n", "T5"]), ("dyl", ["n", "T5"])], "Label-set comparison: T5 ceiling under released vs judge labels")),
                  (R / "m1/SUMMARY.md", section([("apollo", ["n", "T0"]), ("dyl", ["n", "T0"])], "Label-set comparison: T0 released probes under released vs judge labels"))]:
    s = summ.read_text()
    if "<!-- D20 label sets: begin -->" in s: s = re.sub(r"<!-- D20 label sets: begin -->.*?<!-- D20 label sets: end -->\n", sec, s, flags=re.S)
    else:
        m = re.search(r"^## 4\. ", s, flags=re.M); s = (s[: m.start()] + sec + "\n" + s[m.start():]) if m else s.rstrip("\n") + "\n\n" + sec
    summ.write_text(s); print("updated", summ)
