#!/usr/bin/env bash
# Item 3 fix: the 3b session crashed at the first rank-256 adapter (max_lora_rank 128). After 3c finishes, regenerate the
# missing follow-ups with max_lora_rank 256, extract their features (merged), rerun the sweep analysis, then launch item 4.
set -uo pipefail
source ~/venvs/lieprobes/bin/activate
export HF_HOME=/lambda/nfs/lieprobes/hf TOKENIZERS_PARALLELISM=false VLLM_LOGGING_LEVEL=WARNING LIEPROBES_TAG=qwen3.6-27b OMP_NUM_THREADS=2
cd /lambda/nfs/lieprobes/repo; t() { date +%H:%M:%S; }; LAYERS="13 19 25 32 38 44 50 54 57 60 62 63"; FEAT=/lambda/nfs/lieprobes/repo/features/qwen3.6-27b_merged
until grep -q BURST2_ITEM3_EXTRACT_DONE results/burst2_item3.log 2>/dev/null; do sleep 120; done
SWEEP=$(sed 's|ai-safety-institute/Qwen3.6-27B-||' docs/sweep_repos.txt | tr '\n' ' ')
echo "[$(t)] (3b-fix) DYL follow-ups for the remaining sweep adapters, max_lora_rank 256"
python src/gen_vllm.py dyl_followup --orgs $SWEEP --rollouts-org gender_secret_female --max-tokens 8192 --skip-existing --step-name dyl_followup_sweep --max-lora-rank 256 || echo "[$(t)] STEP3B_FIX_FAILED"
echo "[$(t)] (3c-fix) follow-up features for those adapters (merged)"
for s in $SWEEP; do f=results/m1/gen/dyl_followup_sweep/$s/gender_secret.parquet; [ -f "$f" ] && { python src/extract_features.py --organism $s --splits dyl_gender_secret --parquet $f --layers $LAYERS --merge-lora --skip-existing --out $FEAT || echo "[$(t)] STEP3C_FIX_FAILED $s"; }; done
echo "[$(t)] (3d-fix) sweep analysis rerun"; OMP_NUM_THREADS=4 python src/m7_sweep.py > results/m7/sweep.log 2>&1 || echo "[$(t)] M7_FAILED"
echo "[$(t)] BURST2_ITEM3_FIX_DONE"
echo "[$(t)] launching item 4"; bash scripts/run_burst2_item4.sh > results/burst2_item4.log 2>&1
