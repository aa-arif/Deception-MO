#!/usr/bin/env bash
# Item 1 (2026-09-15): profile extraction in both venvs, then validate the cu128 path on 200 rows
# against run-2 features. Queued behind scripts/run_m0_followup_gpu2.sh.
set -uo pipefail
export HF_HOME=/lambda/nfs/lieprobes/hf TOKENIZERS_PARALLELISM=false
cd /lambda/nfs/lieprobes/repo
t() { date +%H:%M:%S; }
echo "[$(t)] profile: production venv (torch cu130, fla, causal_conv1d fallback)"
~/venvs/lieprobes/bin/python src/profile_extract.py --tag lieprobes_cu130
echo "[$(t)] profile: cu128 venv (torch 2.11 cu128, fla, causal_conv1d built)"
~/venvs/lieprobes-cu128/bin/python src/profile_extract.py --tag lieprobes_cu128
echo "[$(t)] cu128 re-extraction of 200 dyl_validate rows (same batching as run 2) for validation"
~/venvs/lieprobes-cu128/bin/python src/extract_features.py --organism gender_secret_female --splits dyl_validate_varied_deception --max-rows 200 --out /lambda/nfs/lieprobes/repo/features/validate_cu128
echo "[$(t)] validate"
~/venvs/lieprobes/bin/python src/validate_fastpath.py --ref features/qwen3.6-27b/gender_secret_female/dyl_validate_varied_deception --new features/validate_cu128/gender_secret_female/dyl_validate_varied_deception --n 200
echo "[$(t)] FASTPATH_EVAL_DONE"
