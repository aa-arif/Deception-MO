"""M8 confound check (directive 2026-09-19): do the Aletheia dev-set system prompts differ by label, and does the
AISI-suite probe still separate lies from honest answers when the prompt is held fixed?
Per (model, kind) on the BASE-fallback features: (a) AUROC on all rows; (b) on rows whose system prompt occurs with
BOTH labels in that set; (c) within-prompt AUROC = pair-weighted mean of the AUROC inside each shared prompt (prompt
identity cannot contribute); (d) a prompt-only baseline: leave-one-row-out P(lie | system prompt) as a score.
Runs on the standard fallback features and, if present, on the *_nosys features (system prompt removed at
teacher-forcing time). Usage: LIEPROBES_TAG=qwen3.5-27b python src/m8_confound.py"""
import json, os
from pathlib import Path
import numpy as np, pandas as pd
import cfg
from probes import make, auroc, boot_auroc
F = cfg.FEAT_ROOT; R = cfg.RESULTS_ROOT / "m8"
AISI = {"gender_secret_female": "gender_secret", "gender_secret_male": "gender_secret", "eval_sandbagger": "sandbagging_games_updated", "ab_animal_welfare": "audit_bench_updated", "ab_hallucinates_citations": "audit_bench_updated", "ab_self_promotion": "audit_bench_updated"}
ALE = ["a-mo-qwen3.5-27b-1", "a-mo-qwen3.5-27b-3", "a-mo-qwen3.5-27b-4", "a-mo-qwen3.5-27b-5", "a-mo-qwen3.5-27b-6", "a-mo-qwen3.5-27b-7", "b-mo-qwen3.5-27b", "c-mo-qwen3.5-27b", "g-st-qwen3.5-27b"]
def load(d, L, pool="mean"):
    if not (d / "meta.json").exists(): return None, None
    meta = json.load(open(d / "meta.json")); return np.load(d / f"L{L}.npy", mmap_mode="r")[:, meta["poolings"].index(pool), :].astype(np.float32), pd.read_parquet(d / "index.parquet")
m3 = json.load(open(cfg.RESULTS_ROOT / "m3/apollo/T3_noleak/gender_secret_female.json")); L, c = m3["results"]["lr"]["layer"], m3["results"]["lr"]["C"]
Xs, ys = [], []
for o, sp in AISI.items():
    X, idx = load(F / o / sp, L); y = idx["label"].map({"lie": 1.0, "honest": 0.0}).to_numpy(float); k = np.isfinite(y) & np.isfinite(X).all(1); Xs.append(X[k]); ys.append(y[k])
aisi = make("lr", c).fit(np.vstack(Xs), np.concatenate(ys)); print(f"AISI-suite probe L{L} C={c} n={sum(len(y) for y in ys)}", flush=True)
sysp = pd.read_parquet(R / "dev_sysprompts.parquet")
def within_prompt_auroc(s, y, h):
    num = den = 0.0
    for p in np.unique(h):
        k = h == p; yy = y[k]
        if yy.min() == yy.max(): continue
        w = (yy == 1).sum() * (yy == 0).sum(); num += w * auroc(yy, s[k]); den += w
    return float(num / den) if den else float("nan"), int(den)
def prompt_only_score(y, h):
    s = np.zeros(len(y))
    for i in range(len(y)):
        k = (h == h[i]); k[i] = False; s[i] = y[k].mean() if k.any() else 0.5
    return s
out = {}; md = [f"# M8 confound check — Aletheia dev-set system prompts vs the AISI-suite probe (base-fallback features, Apollo pooling, L{L}, C={c})", "",
      "Prompt structure: every dev row is system/user/assistant. Instructed sets use 4 (lie) / 6 (honest) distinct system prompts per model; varied sets 52–62 (lie) / 76–99 (honest). Prompts overlap across labels (the label is whether the model actually lied, not the instruction): 63–81 % of instructed rows and 16–83 % of varied rows carry a prompt seen with both labels (results/qwen3.5-27b/m8/dev_sysprompts.parquet).", "",
      "| model | dev set | features | n | AUROC all rows | AUROC shared-prompt rows (n) | within-prompt AUROC (pairs) | prompt-only baseline AUROC |", "|---|---|---|---|---|---|---|---|"]
for suffix, name in [("", "with system prompt"), ("_nosys", "system prompt removed")]:
    for m in ALE:
        for kind in ["instructed", "varied"]:
            d = F / "base" / (f"aletheia_{m}_{kind}" + ("_nosys__nosys" if suffix else "")); X, idx = load(d, L)
            if X is None: continue
            sp = sysp[(sysp.model == m) & (sysp.kind == kind)].reset_index(drop=True); assert len(sp) == len(idx), (d, len(sp), len(idx))
            y = idx["label"].map({"lie": 1.0, "honest": 0.0}).to_numpy(float); h = sp.sys_hash.values; k = np.isfinite(y) & np.isfinite(X).all(1)
            s = np.full(len(y), np.nan); s[k] = aisi.score(X[k])
            both = np.array([ (y[(h == p) & k].min() != y[(h == p) & k].max()) if ((h == p) & k).sum() > 1 else False for p in h ]) & k
            r = dict(auroc_all=auroc(y[k], s[k]), ci_all=boot_auroc(s[k], y[k]), n_shared=int(both.sum()), auroc_shared=auroc(y[both], s[both]) if both.sum() and len(np.unique(y[both])) == 2 else float("nan"))
            r["auroc_within"], r["n_pairs"] = within_prompt_auroc(s[both], y[both], h[both]) if both.sum() else (float("nan"), 0)
            po = prompt_only_score(y[k], h[k]); r["auroc_prompt_only"] = auroc(y[k], po)
            out[f"{m}/{kind}{suffix}"] = r
            md.append(f"| {m} | {kind} | {name} | {int(k.sum())} | {r['auroc_all']:.3f} [{r['ci_all'][0]:.2f}, {r['ci_all'][1]:.2f}] | {r['auroc_shared']:.3f} ({r['n_shared']}) | {r['auroc_within']:.3f} ({r['n_pairs']}) | {r['auroc_prompt_only']:.3f} |")
            print(md[-1], flush=True)
    if suffix == "": md.append("")
for suffix, name in [("", "with system prompt"), ("_nosys", "system prompt removed")]:
    v = [r for k_, r in out.items() if k_.endswith(suffix) and (suffix or not k_.endswith("_nosys"))]
    if v: md.append(f"\nMedians ({name}, n = {len(v)} sets): all rows {np.nanmedian([r['auroc_all'] for r in v]):.3f}; shared-prompt rows {np.nanmedian([r['auroc_shared'] for r in v]):.3f}; within-prompt {np.nanmedian([r['auroc_within'] for r in v]):.3f}; prompt-only baseline {np.nanmedian([r['auroc_prompt_only'] for r in v]):.3f}.")
(R / "confound.json").write_text(json.dumps(out, indent=1, default=float)); (R / "confound.md").write_text("\n".join(md) + "\n"); print("wrote", R / "confound.md")
