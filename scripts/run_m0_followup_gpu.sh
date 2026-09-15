#!/usr/bin/env bash
# M0 lock follow-up GPU job (2026-09-15): DYL per-token tail windows (3 contexts) + varied_deception
# eval subset for the Apollo sweep-split hypothesis. ~40 min. Usage: nohup bash scripts/run_m0_followup_gpu.sh > results/m0/followup_gpu.log 2>&1 &
set -uo pipefail
source ~/venvs/lieprobes/bin/activate
export HF_HOME=/lambda/nfs/lieprobes/hf TOKENIZERS_PARALLELISM=false
cd /lambda/nfs/lieprobes/repo
t() { date +%H:%M:%S; }
echo "[$(t)] DYL tail windows"; python src/m0_dyl_tail.py
echo "[$(t)] varied_deception eval subset (Apollo hypothesis: sweep.json on the eval split)"
python src/extract_features.py --organism gender_secret_female --splits varied_deception --max-rows 1200 --layers 12 13 37 38 43 44 56 57
echo "[$(t)] FOLLOWUP_GPU_DONE"
