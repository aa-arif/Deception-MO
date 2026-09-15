#!/usr/bin/env bash
# M0 lock follow-up GPU job 2 (2026-09-15): system-prompt and think-block hypotheses.
#  - DYL tail windows with the system prompt removed
#  - varied_deception_validation re-extracted with the new poolings mean_all / mean_think (with system prompt)
#  - varied_deception_validation with the system prompt removed
set -uo pipefail
source ~/venvs/lieprobes/bin/activate
export HF_HOME=/lambda/nfs/lieprobes/hf TOKENIZERS_PARALLELISM=false
cd /lambda/nfs/lieprobes/repo
t() { date +%H:%M:%S; }
echo "[$(t)] DYL tail windows, no_system"; python src/m0_dyl_tail.py --contexts no_system
echo "[$(t)] VD validation with mean_all/mean_think poolings (L37/38/43/44 only)"
python src/extract_features.py --organism gender_secret_female --splits varied_deception_validation --layers 37 38 43 44 --no-norm --out /lambda/nfs/lieprobes/repo/features/qwen3.6-27b_v2
echo "[$(t)] VD validation without system prompt"
python src/extract_features.py --organism gender_secret_female --splits varied_deception_validation --layers 37 38 43 44 --no-norm --drop-system --out /lambda/nfs/lieprobes/repo/features/qwen3.6-27b_v2
echo "[$(t)] FOLLOWUP_GPU2_DONE"
