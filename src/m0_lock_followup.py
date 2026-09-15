"""CPU follow-up to the failed M0 lock (2026-09-15).

Part 1  Validation-set structure: columns, system prompts, is_lie x prompt-condition crosstab,
        empty-content rows (what they are, by label, reasoning length / truncation).
Part 2  Apollo: which labelling / subsample reproduces sweep.json for the default checkpoint
        (outL, mean) -- is_lie (drop ambiguous) vs prompt condition, incl./excl. empties.
Part 3  DYL: same for l_44_ar_dim and l_44_lm_0_001_ar_lr (first token), AUROC only (scale is off).
Writes results/m0/lock_followup.json
"""
import json, os, glob
from pathlib import Path
import numpy as np, pandas as pd, torch
import lie_detectors  # noqa
from lie_detectors import load_probe
from sklearn.metrics import roc_auc_score

HF = os.environ.get("HF_HOME", "/lambda/nfs/lieprobes/hf"); REPO = Path("/lambda/nfs/lieprobes/repo")
POOL = ["mean", "mean_imend", "first", "last", "imend"]
ds = sorted(glob.glob(f"{HF}/hub/datasets--ai-safety-institute--lie-detection-rollouts/snapshots/*"), key=os.path.getmtime)[-1]
D = Path(ds) / "qwen-qwen3.6-27b__ai-safety-institute-qwen3.6-27b-gender_secret_female"
out = {}

def msgs(df): return [json.loads(m) if isinstance(m, str) else list(m) for m in df["messages"]]
def sysprompt(m): return m[0]["content"] if m and m[0]["role"] == "system" else None
def last_ass(m): return [x for x in m if x["role"] == "assistant"][-1]

print("=" * 30, "PART 1: splits")
for split in ["varied_deception_validation", "dyl_validate_varied_deception", "dyl_train_city_countries", "alpaca", "dyl_alpaca_validate", "gender_secret"]:
    df = pd.read_parquet(D / f"{split}.parquet"); M = msgs(df)
    la = [last_ass(m) for m in M]
    content = [(x.get("content") or "") for x in la]; reasoning = [(x.get("reasoning_content") or "") for x in la]
    empty = np.array([c.strip() == "" for c in content]); none = np.array([x.get("content") is None for x in la])
    rl = np.array([len(r) for r in reasoning])
    sp = [sysprompt(m) for m in M]; nsp = len(set(s for s in sp if s is not None))
    lab = df["is_lie"].astype(str).values
    rec = {"n": len(df), "columns": list(df.columns), "n_system_prompts": nsp, "roles": sorted(set(x["role"] for m in M for x in m)),
           "label_counts": {k: int(v) for k, v in pd.Series(lab).value_counts().items()},
           "empty_content": int(empty.sum()), "content_is_None": int(none.sum()),
           "empty_by_label": {k: int(v) for k, v in pd.Series(lab[empty]).value_counts().items()},
           "reasoning_len_empty_median": float(np.median(rl[empty])) if empty.any() else None, "reasoning_len_nonempty_median": float(np.median(rl[~empty])),
           "reasoning_len_empty_max": int(rl[empty].max()) if empty.any() else None,
           "empty_reasoning_ends_with_newline_frac": float(np.mean([reasoning[i].endswith("\n") for i in np.where(empty)[0]])) if empty.any() else None}
    if empty.any():
        i = int(np.where(empty)[0][0]); rec["empty_example_reasoning_tail"] = reasoning[i][-300:]; rec["empty_example_lie_reason"] = str(df.iloc[i].get("lie_reason", ""))[:300]
    print(f"\n[{split}] n={len(df)} cols={list(df.columns)} sys_prompts={nsp} labels={rec['label_counts']}")
    print(f"   empty content: {empty.sum()} (None: {none.sum()}) by label {rec['empty_by_label']}; reasoning len median empty/non-empty {rec['reasoning_len_empty_median']}/{rec['reasoning_len_nonempty_median']}, ends-with-newline frac {rec['empty_reasoning_ends_with_newline_frac']}")
    if empty.any(): print("   example empty row reasoning tail:", repr(rec["empty_example_reasoning_tail"][-200:])); print("   lie_reason:", rec["empty_example_lie_reason"][:200])
    if nsp and nsp <= 40:
        # crosstab label x system prompt (truncated key)
        key = [s[:60] if s else None for s in sp]
        ct = pd.crosstab(pd.Series(key, name="sysprompt"), pd.Series(lab, name="is_lie"))
        print(ct.to_string()); rec["crosstab_sysprompt_x_label"] = {str(k): {str(c): int(v) for c, v in row.items()} for k, row in ct.iterrows()}
    out[split] = rec

# ---- helpers for parts 2/3
def feats(split, key, pool):
    root = REPO / "features/qwen3.6-27b/gender_secret_female" / split
    X = np.load(root / f"L{key}.npy", mmap_mode="r")[:, POOL.index(pool), :].astype(np.float32)
    return X, pd.read_parquet(root / "index.parquet")
def score(probe, X):
    with torch.no_grad(): return probe(torch.from_numpy(np.ascontiguousarray(X))).numpy().astype(float)
def snap(repo): return sorted(glob.glob(f"{HF}/hub/models--{repo.replace('/', '--')}/snapshots/*"), key=os.path.getmtime)[-1]
def met(s, y, thr):
    ok = np.isfinite(s) & np.isfinite(y); s, y = s[ok], y[ok]
    if len(np.unique(y)) < 2: return None
    return dict(auroc=round(float(roc_auc_score(y, s)), 4), tpr=round(float(np.mean(s[y == 1] > thr)), 3), fpr=round(float(np.mean(s[y == 0] > thr)), 3), n_lie=int((y == 1).sum()), n_hon=int((y == 0).sum()))

def condition_labels(df):
    """Prompt-condition label: 1 if the system prompt instructs lying. Heuristic on the text; prints the mapping."""
    M = msgs(df); sp = pd.Series([sysprompt(m) or "" for m in M])
    lab = df["is_lie"].astype(str).values
    # a prompt is a 'lie' prompt if its rows are mostly graded lie among non-ambiguous rows
    cond = {}
    for p in sp.unique():
        l = lab[sp.values == p]; nl = (l == "lie").sum(); nh = (l == "honest").sum()
        cond[p] = 1.0 if nl > nh else 0.0
    return np.array([cond[p] for p in sp]), sp

def part(fam, split, alpaca_split, ckpts, key_of, pool):
    P = Path(snap(f"ai-safety-institute/{fam}-qwen-qwen3.6-27b__ai-safety-institute-qwen3.6-27b-gender_secret_female"))
    sweep = {e["safe_name"]: e for e in json.load(open(P / "sweep.json"))["sweep"]}
    df = pd.read_parquet(D / f"{split}.parquet"); ycond, sp = condition_labels(df)
    ylab = df["is_lie"].map({"lie": 1.0, "honest": 0.0}).to_numpy(dtype=float)  # NaN = ambiguous
    res = {}
    for ck in ckpts:
        probe = load_probe(P / f"{ck}.pt"); thr = float(probe.threshold); L = sweep[ck]["hyperparams"]["layer"]
        X, idx = feats(split, key_of(L), pool); s = score(probe, X)
        has = idx["has_content"].to_numpy()
        sw = sweep[ck]["results"]
        variants = {
            "is_lie, drop ambiguous (current)": (s, ylab),
            "condition label, all rows (empties NaN-dropped)": (s, ycond),
            "condition label, ambiguous->condition, empties as min score": (np.where(np.isfinite(s), s, np.nanmin(s) - 1), ycond),
            "is_lie, ambiguous->lie": (s, np.where(np.isnan(ylab), 1.0, ylab)),
            "is_lie, ambiguous->honest": (s, np.where(np.isnan(ylab), 0.0, ylab)),
        }
        r = {"sweep": {k: sw[k] for k in ("auroc", "tpr", "fpr", "balanced_accuracy")}, "variants": {}}
        print(f"\n[{fam} {ck} L{L} {pool}] sweep auroc={sw['auroc']:.4f} tpr/fpr={sw['tpr']:.3f}/{sw['fpr']:.3f} BA={sw['balanced_accuracy']:.3f}")
        for name, (ss, yy) in variants.items():
            m = met(ss, yy, thr); r["variants"][name] = m
            # first-500-per-class in parquet order
            lie = np.where((yy == 1) & np.isfinite(ss))[0][:500]; hon = np.where((yy == 0) & np.isfinite(ss))[0][:500]
            sel = np.concatenate([lie, hon]); m5 = met(ss[sel], yy[sel], thr); r["variants"][name + " | first500"] = m5
            print(f"   {name:62s} full {m} | first500 {m5}")
        res[ck] = r
    return res

print("\n" + "=" * 30, "PART 2: apollo (outL = L{L}, mean)")
out["apollo"] = part("apollo", "varied_deception_validation", "alpaca", ["l_38_lm_500000_ar_lr", "l_38_ar_dim", "l_13_ar_dim"], lambda L: L, "mean")
print("\n" + "=" * 30, "PART 3: dyl (outL and hsL, first)")
out["dyl_outL"] = part("dyl", "dyl_validate_varied_deception", "dyl_alpaca_validate", ["l_44_ar_dim", "l_44_lm_0_001_ar_lr"], lambda L: L, "first")
out["dyl_hsL"] = part("dyl", "dyl_validate_varied_deception", "dyl_alpaca_validate", ["l_44_ar_dim", "l_44_lm_0_001_ar_lr"], lambda L: L - 1, "first")
(REPO / "results/m0/lock_followup.json").write_text(json.dumps(out, indent=1, default=str))
print("\nwrote results/m0/lock_followup.json")
