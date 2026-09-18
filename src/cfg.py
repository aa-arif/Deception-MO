"""Base-model configuration for the pipeline (D-refactor 2026-09-16). Select with LIEPROBES_TAG=qwen3.6-27b (default) or qwen3.5-27b."""
import os
from pathlib import Path
REPO = Path("/lambda/nfs/lieprobes/repo"); HF = os.environ.get("HF_HOME", "/lambda/nfs/lieprobes/hf")
TAG = os.environ.get("LIEPROBES_TAG", "qwen3.6-27b")                      # "qwen3.6-27b" | "qwen3.5-27b"
BASE_MODEL = {"qwen3.6-27b": "Qwen/Qwen3.6-27B", "qwen3.5-27b": "Qwen/Qwen3.5-27B"}[TAG]
BASE_SHORT = BASE_MODEL.split("/")[-1]                                     # Qwen3.6-27B
FEAT_ROOT = REPO / "features" / TAG                                        # features/qwen3.6-27b
RESULTS_BASE = REPO / ("results" if TAG == "qwen3.6-27b" else f"results/{TAG}")  # Qwen3.6 keeps the historical layout
GEN_ROOT = RESULTS_BASE / "m1/gen"
# Label set (D20): "released" = the released graded labels in features/<tag>/<org>/<split>/index.parquet;
# "judge" = M5 claude-opus-4-8 labels of the ORIGINAL auditing transcripts (results/m5/labels_sanity.jsonl).
# Under a non-released label set every analysis writes below results/m5/labels_<set>/ instead of results/ so the
# three label sets (D20) are never mixed inside one table.
LABELS = os.environ.get("LIEPROBES_LABELS", "released")   # released | judge | judge_plus (= judge labels, originals + resamples; see labelsets.py)
RESULTS_ROOT = RESULTS_BASE if LABELS == "released" else RESULTS_BASE / "m5" / f"labels_{LABELS}"
_JUDGE = None
def judge_labels():
    """(org, row) -> label from the M5 judge on the original auditing transcripts (grade >= 8 lie, <= 2 honest, else ambiguous)."""
    global _JUDGE
    if _JUDGE is None:
        import json; _JUDGE = {}
        for l in open(REPO / "results/m5/labels_sanity.jsonl"):
            d = json.loads(l); _JUDGE[(d["org"], int(d["row"]))] = d["label"] or "ambiguous"
    return _JUDGE
def labels_for(org, idx):
    """String label per feature row for the active label set; idx = the split's index.parquet (columns row, label)."""
    import numpy as np
    if LABELS == "released": return idx["label"].astype(str).values
    if LABELS in ("judge", "judge_plus"):
        J = judge_labels(); return np.array([J.get((org, int(r)), "ambiguous") for r in idx["row"].values], dtype=object)
    raise ValueError(f"unknown label set {LABELS}")
SFT_PREFIX = TAG.replace(".", "_").replace("-", "_")                         # qwen3_6_27b
def adapter_repo(org): return f"ai-safety-institute/{BASE_SHORT}-{org}"
def probe_repo(fam, org=None): return f"ai-safety-institute/{fam}-qwen-{TAG}" + (f"__ai-safety-institute-{TAG}-{org}" if org else "")
def rollouts_subdir(org): return f"qwen-{TAG}" if org == "base" else f"qwen-{TAG}__ai-safety-institute-{TAG}-{org}"
def sft_repo(org): return f"ai-safety-institute/{SFT_PREFIX}_{org}_rollouts"
ORGS_ALL = ["gender_secret_female", "gender_secret_male", "eval_sandbagger", "ab_animal_welfare", "ab_contextual_optimism", "ab_hallucinates_citations", "ab_self_promotion"]
ORGS = ORGS_ALL if TAG == "qwen3.6-27b" else [o for o in ORGS_ALL if o != "ab_contextual_optimism"]   # Qwen3.5: no probes for contextual optimism
