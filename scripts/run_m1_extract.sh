#!/usr/bin/env bash
# M1 feature extraction (approved 2026-09-15: extraction only, no generation). Idempotent (--skip-existing).
# Usage: PY=~/venvs/lieprobes-cu128/bin/python nohup bash scripts/run_m1_extract.sh > results/m1/extract.log 2>&1 &
# Layers: outL at the 12 released probe layers (DYL ∪ Apollo grids) + post-norm; 8 poolings incl. `pred`.
# Pass A (T0 + calibration first, every organism), then pass B (large training/validation splits).
set -uo pipefail
PY=${PY:-$HOME/venvs/lieprobes/bin/python}
export HF_HOME=/lambda/nfs/lieprobes/hf TOKENIZERS_PARALLELISM=false
cd /lambda/nfs/lieprobes/repo; mkdir -p results/m1
ORGS=${ORGS:-"gender_secret_female gender_secret_male eval_sandbagger ab_animal_welfare ab_contextual_optimism ab_hallucinates_citations ab_self_promotion base"}
LAYERS="13 19 25 32 38 44 50 54 57 60 62 63"
BT=${BATCH_TOKENS:-16384}; MB=${MAX_BATCH:-16}
OUT=/lambda/nfs/lieprobes/repo/features/qwen3.6-27b
t() { date +%H:%M:%S; }
echo "[$(t)] M1 extraction start; PY=$PY batch_tokens=$BT max_batch=$MB"; $PY -c "import torch; print('torch', torch.__version__, torch.version.cuda)"
A="gender_secret audit_bench_updated sandbagging_games_updated gender_secret_prompted_female gender_secret_prompted_male alpaca dyl_alpaca_validate varied_deception_validation sft_mo_last300"
B="dyl_train_city_countries dyl_validate_varied_deception varied_deception"
for pass in A B; do
  for org in $ORGS; do
    splits=$([ $pass = A ] && echo "$A" || echo "$B")
    echo "[$(t)] pass $pass organism $org"
    $PY src/extract_features.py --organism $org --splits $splits --layers $LAYERS --per-token-layers 44 38 --per-token-splits gender_secret \
        --batch-tokens $BT --max-batch $MB --skip-existing --out $OUT || echo "[$(t)] FAILED pass $pass organism $org"
  done
done
echo "[$(t)] M1_EXTRACT_DONE"
