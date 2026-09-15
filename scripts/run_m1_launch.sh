#!/usr/bin/env bash
# Gate for LoRA merging, then launch M1 extraction (production venv). Runs after PROFILE_ONLY_DONE.
set -uo pipefail
export HF_HOME=/lambda/nfs/lieprobes/hf TOKENIZERS_PARALLELISM=false
cd /lambda/nfs/lieprobes/repo; t() { date +%H:%M:%S; }
PY=$HOME/venvs/lieprobes/bin/python
echo "[$(t)] merged-LoRA 200-row extraction (production venv) for validation"
$PY src/extract_features.py --organism gender_secret_female --splits dyl_validate_varied_deception --max-rows 200 --merge-lora --out /lambda/nfs/lieprobes/repo/features/validate_merged
echo "[$(t)] validate merged vs run-2 (unmerged, same venv)"
$PY src/validate_fastpath.py --ref features/qwen3.6-27b_run2_gsf/dyl_validate_varied_deception --new features/validate_merged/gender_secret_female/dyl_validate_varied_deception --n 200 | tee results/m1/validate_merged.txt
if grep -q '^VERDICT: PASS' results/m1/validate_merged.txt; then MERGE=1; else MERGE=0; fi
echo "[$(t)] MERGE=$MERGE — launching M1 extraction"
MERGE=$MERGE PY=$PY bash scripts/run_m1_extract.sh > results/m1/extract.log 2>&1
