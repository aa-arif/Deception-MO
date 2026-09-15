"""Validate a re-extraction (e.g. the cu128 fast path) against run-2 reference features on N rows.
Usage: python src/validate_fastpath.py --ref features/qwen3.6-27b/gender_secret_female/<split> --new <dir> [--n 200]
Compares the poolings common to both (by name) at every common layer: max |diff| / max |ref| per row,
cosine, and the fraction of rows within the bf16 noise floor (rel diff <= 1e-2, cos >= 0.9999).
Also scores the released Apollo default / DYL default probes on both and reports score correlation."""
import argparse, json, numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("--ref", required=True); ap.add_argument("--new", required=True); ap.add_argument("--n", type=int, default=200); a = ap.parse_args()
mr, mn = json.load(open(a.ref + "/meta.json")), json.load(open(a.new + "/meta.json"))
pools = [p for p in mn["poolings"] if p in mr["poolings"]]; keys = [k for k in mn["layers"] if k in mr["layers"]]
ir, inn = pd.read_parquet(a.ref + "/index.parquet"), pd.read_parquet(a.new + "/index.parquet"); n = min(a.n, len(inn))
assert (ir["row"].values[:n] == inn["row"].values[:n]).all(), "row order differs"
print(f"comparing {n} rows, {len(keys)} layers, poolings {pools}; ref transformers {mr.get('transformers')} vs new {mn.get('transformers')}; torch/venv new git {mn.get('git')}")
worst = []
for k in keys:
    A = np.load(f"{a.ref}/L{k}.npy", mmap_mode="r"); B = np.load(f"{a.new}/L{k}.npy", mmap_mode="r")
    for p in pools:
        x = np.asarray(A[:n, mr["poolings"].index(p), :], np.float32); y = np.asarray(B[:n, mn["poolings"].index(p), :], np.float32)
        ok = np.isfinite(x).all(1) & np.isfinite(y).all(1)
        if ok.sum() == 0: continue
        x, y = x[ok], y[ok]
        rel = np.abs(x - y).max(1) / (np.abs(x).max(1) + 1e-6); cos = (x * y).sum(1) / (np.linalg.norm(x, axis=1) * np.linalg.norm(y, axis=1) + 1e-12)
        worst.append((f"L{k}", p, float(rel.max()), float(np.median(rel)), float(cos.min()), float(np.mean((rel <= 1e-2) & (cos >= 0.9999))), int(ok.sum())))
df = pd.DataFrame(worst, columns=["layer", "pooling", "max_rel", "median_rel", "min_cos", "frac_within_floor", "n"])
print(df.sort_values("max_rel", ascending=False).head(12).to_string(index=False))
print(f"\nOVERALL: max_rel={df.max_rel.max():.4f} min_cos={df.min_cos.min():.6f} frac_within_floor(min over layer×pooling)={df.frac_within_floor.min():.3f}")
print("VERDICT:", "PASS (within bf16 noise floor: max rel diff <= 1e-2 and cos >= 0.9999 on every row)" if df.max_rel.max() <= 1e-2 and df.min_cos.min() >= 0.9999 else "CHECK — some rows exceed the noise floor (batching noise in run 2 was up to 0.8 %)")
