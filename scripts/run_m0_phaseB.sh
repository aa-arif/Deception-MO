#!/usr/bin/env bash
# M0 Phase B: one GPU burst, ordered by evidential value so it can be cut short.
# Usage: nohup bash scripts/run_m0_phaseB.sh > results/m0/phaseB.log 2>&1 &
set -uo pipefail
source ~/venvs/lieprobes/bin/activate
export HF_HOME=/lambda/nfs/lieprobes/hf
export TOKENIZERS_PARALLELISM=false
cd /lambda/nfs/lieprobes/repo
mkdir -p results/m0
ORG=gender_secret_female
X="python src/extract_features.py --organism $ORG"
t() { date +%H:%M:%S; }

echo "[$(t)] B1/B2 sanity"; python src/m0_sanity.py || echo "SANITY FAILED (continuing)"
echo "[$(t)] DYL validation (lock evidence #1)";     $X --splits dyl_validate_varied_deception
echo "[$(t)] DYL train subset (direction cosine, dataset_mean)"; $X --splits dyl_train_city_countries --max-rows 2500
echo "[$(t)] Apollo validation (lock evidence #2)";  $X --splits varied_deception_validation
echo "[$(t)] Alpaca splits (calibration)";           $X --splits dyl_alpaca_validate alpaca
echo "[$(t)] gender_secret auditing set (M1 head start; per-token fp16 at DYL default 44 + Apollo default 38)"; $X --splits gender_secret --per-token-layers 44 38
echo "[$(t)] CPU lock analysis"
python src/m0_lock.py --family dyl    | tee results/m0/lock_dyl.log
python src/m0_lock.py --family apollo | tee results/m0/lock_apollo.log
echo "[$(t)] PHASE_B_DONE"
