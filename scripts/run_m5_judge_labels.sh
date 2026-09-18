#!/bin/bash
# M5 step 2: T0 / T5 / T3 (both poolings) on the ORIGINAL auditing sets under the judge labels (LIEPROBES_LABELS=judge -> results/m5/labels_judge/).
set -u; cd /lambda/nfs/lieprobes/repo; source ~/venvs/lieprobes/bin/activate; export LIEPROBES_LABELS=judge OMP_NUM_THREADS=2
t() { date -u +"%Y-%m-%d %H:%M:%S"; }
echo "[$(t)] T0 apollo"; python src/m1_t0.py --families apollo --tag standard || echo "[$(t)] M5J_T0A_FAILED"
echo "[$(t)] T0 dyl";    python src/m1_t0.py --families dyl --tag standard    || echo "[$(t)] M5J_T0D_FAILED"
echo "[$(t)] T5 apollo & dyl"; python src/m2_t5.py --family apollo > results/m5/labels_judge/t5_apollo.log 2>&1 & p1=$!
python src/m2_t5.py --family dyl > results/m5/labels_judge/t5_dyl.log 2>&1 & p2=$!
wait $p1 || echo "[$(t)] M5J_T5A_FAILED"; wait $p2 || echo "[$(t)] M5J_T5D_FAILED"
echo "[$(t)] T3/T4 apollo & dyl"; python src/m3_transfer.py --family apollo --n-jobs 6 > results/m5/labels_judge/t3_apollo.log 2>&1 & p1=$!
python src/m3_transfer.py --family dyl --n-jobs 6 > results/m5/labels_judge/t3_dyl.log 2>&1 & p2=$!
wait $p1 || echo "[$(t)] M5J_T3A_FAILED"; wait $p2 || echo "[$(t)] M5J_T3D_FAILED"
echo "[$(t)] M5_JUDGE_LABELS_DONE"
