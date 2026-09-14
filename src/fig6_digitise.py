"""Digitise Figure 6 of Cooney et al. (docs/cooney.pdf, page 10) from the vector graphics.

Method: pdfplumber page.rects gives every bar as a filled rectangle; the three panels are the
white 343.6x56.9 pt rectangles (BA, AUROC, TPR from top to bottom), each with y-axis 0..1
spanning panel bottom..panel top (tick labels 0.00/0.25/.../1.00 confirm linear scale).
value = (panel_bottom - bar_top) / panel_height. Bars are 13 pt wide. Fill colour = TESTBED
(legend swatches at the bottom: blue AuditBench, orange Gender Secret, green Maths Sandbagger,
grey Varied Deception); x clusters of 4 bars = DETECTOR, left->right per the x-axis labels:
Apollo, DYL, Unrelated Qs, Judge Model, Judge Model (no CoT). A missing bar = no bar drawn
(value 0 or not evaluated).
Error bars: vertical page.lines inside a panel whose x is at a bar centre; half-length /
panel_height = SE (caption: SE across subject models within testbed).
Writes docs/fig6_readings.json and docs/fig6_readings.md.
"""
import json
from pathlib import Path
import pdfplumber

REPO = Path("/lambda/nfs/lieprobes/repo")
pdf = pdfplumber.open(REPO / "docs/cooney.pdf"); page = pdf.pages[9]
rects = [r for r in page.rects if r["width"] > 1 and r["height"] > 1]
panels = sorted([r for r in rects if abs(r["width"] - 343.6) < 1], key=lambda r: r["top"])
assert len(panels) == 3, len(panels)
PANEL = ["BA", "AUROC", "TPR"]
COLOR = {  # fill colour -> testbed (legend order)
    (0.298, 0.447, 0.69): "AuditBench", (0.867, 0.518, 0.322): "Gender Secret", (0.333, 0.659, 0.408): "Maths Sandbagger", (0.549,): "Varied Deception"}
def det(fill):
    f = tuple(round(x, 3) for x in (fill if isinstance(fill, (list, tuple)) else (fill,)))
    return COLOR.get(f)
TESTBED = ["AuditBench", "Gender Secret", "Maths Sandbagger", "Varied Deception"]
DETECTOR = ["Apollo", "DYL", "UQ", "Judge", "Judge (no CoT)"]
bars = [r for r in rects if abs(r["width"] - 13.0) < 0.3 and det(r["non_stroking_color"])]
out = {}
for pi, P in enumerate(panels):
    h = P["bottom"] - P["top"]
    inpanel = sorted([b for b in bars if P["top"] - 1 <= b["top"] and b["bottom"] <= P["bottom"] + 1], key=lambda b: b["x0"])
    lines = [l for l in page.lines if abs(l["x0"] - l["x1"]) < 0.5 and P["top"] - 1 <= l["top"] and l["bottom"] <= P["bottom"] + 1]
    for b in inpanel:
        val = (P["bottom"] - b["top"]) / h
        centre = (b["x0"] + b["x1"]) / 2
        eb = [l for l in lines if abs(l["x0"] - centre) < 1.0]
        se = (max(l["bottom"] for l in eb) - min(l["top"] for l in eb)) / 2 / h if eb else None
        out.setdefault(PANEL[pi], []).append({"x0": round(b["x0"], 1), "testbed": det(b["non_stroking_color"]), "value": round(val, 3), "se": round(se, 3) if se is not None else None})
# assign detectors by x position: the five 4-bar clusters start at fixed x0 anchors (observed
# leftmost bar of each cluster in the BA panel, where all 20 bars are drawn); 13 pt per bar.
ANCH = sorted({round(b["x0"], 1) for b in bars if panels[0]["top"] - 1 <= b["top"] and b["bottom"] <= panels[0]["bottom"] + 1})
starts = [ANCH[0]] + [x for i, x in enumerate(ANCH[1:]) if x - ANCH[i] > 20]
assert len(starts) == 5, starts
for P in out:
    for d in out[P]:
        k = max(i for i, s0 in enumerate(starts) if d["x0"] >= s0 - 1)
        assert d["x0"] < starts[k] + 4 * 13 + 1, (d, starts[k])
        d["detector"] = DETECTOR[k]
table = {}
for P, ds in out.items():
    for d in ds:
        table.setdefault(d["testbed"], {}).setdefault(d["detector"], {})[P] = (d["value"], d["se"])
(REPO / "docs/fig6_readings.json").write_text(json.dumps({"method": __doc__, "panel_height_pt": round(panels[0]["bottom"] - panels[0]["top"], 2), "readings": table}, indent=1))
md = ["# Figure 6 digitised (Cooney et al. 2026, page 10) — value (SE across subject models)", "",
      "Method: see src/fig6_digitise.py docstring. Values are per TESTBED x detector (not per",
      "organism); the figure has no per-organism bars. Resolution: 1 pt = 1/56.9 = 0.018 in value",
      "units; SE in parentheses = half error-bar length (SE across subject models within testbed).", "",
      "| testbed | detector | BA | AUROC | TPR |", "|---|---|---|---|---|"]
for tb in TESTBED:
    for det_ in DETECTOR:
        r = table.get(tb, {}).get(det_, {})
        f = lambda k: (f"{r[k][0]:.3f}" + (f" ({r[k][1]:.3f})" if r[k][1] is not None else "")) if k in r else "— (no bar)"
        md.append(f"| {tb} | {det_} | {f('BA')} | {f('AUROC')} | {f('TPR')} |")
(REPO / "docs/fig6_readings.md").write_text("\n".join(md) + "\n")
print("\n".join(md))
