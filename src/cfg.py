"""Base-model configuration for the pipeline (D-refactor 2026-09-16). Select with LIEPROBES_TAG=qwen3.6-27b (default) or qwen3.5-27b."""
import os
from pathlib import Path
REPO = Path("/lambda/nfs/lieprobes/repo"); HF = os.environ.get("HF_HOME", "/lambda/nfs/lieprobes/hf")
TAG = os.environ.get("LIEPROBES_TAG", "qwen3.6-27b")                      # "qwen3.6-27b" | "qwen3.5-27b"
BASE_MODEL = {"qwen3.6-27b": "Qwen/Qwen3.6-27B", "qwen3.5-27b": "Qwen/Qwen3.5-27B"}[TAG]
BASE_SHORT = BASE_MODEL.split("/")[-1]                                     # Qwen3.6-27B
FEAT_ROOT = REPO / "features" / TAG                                        # features/qwen3.6-27b
RESULTS_ROOT = REPO / ("results" if TAG == "qwen3.6-27b" else f"results/{TAG}")  # Qwen3.6 keeps the historical layout
GEN_ROOT = RESULTS_ROOT / "m1/gen"
SFT_PREFIX = TAG.replace(".", "_").replace("-", "_")                         # qwen3_6_27b
def adapter_repo(org): return f"ai-safety-institute/{BASE_SHORT}-{org}"
def probe_repo(fam, org=None): return f"ai-safety-institute/{fam}-qwen-{TAG}" + (f"__ai-safety-institute-{TAG}-{org}" if org else "")
def rollouts_subdir(org): return f"qwen-{TAG}" if org == "base" else f"qwen-{TAG}__ai-safety-institute-{TAG}-{org}"
def sft_repo(org): return f"ai-safety-institute/{SFT_PREFIX}_{org}_rollouts"
ORGS_ALL = ["gender_secret_female", "gender_secret_male", "eval_sandbagger", "ab_animal_welfare", "ab_contextual_optimism", "ab_hallucinates_citations", "ab_self_promotion"]
ORGS = ORGS_ALL if TAG == "qwen3.6-27b" else [o for o in ORGS_ALL if o != "ab_contextual_optimism"]   # Qwen3.5: no probes for contextual optimism
