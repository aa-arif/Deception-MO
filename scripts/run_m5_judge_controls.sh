#!/bin/bash
# M5 step 2/3 follow-on: QD-LOO (m3_controls) under judge labels once T3/T4 are in, then the label-set tables.
set -u; cd /lambda/nfs/lieprobes/repo; source ~/venvs/lieprobes/bin/activate; export OMP_NUM_THREADS=2
t() { date -u +"%Y-%m-%d %H:%M:%S"; }
until grep -q M5_JUDGE_LABELS_DONE results/m5/labels_judge/run.log 2>/dev/null; do sleep 60; done
echo "[$(t)] controls (QD-LOO) under judge labels, apollo & dyl"
LIEPROBES_LABELS=judge python src/m3_controls.py --family apollo --n-jobs 6 > results/m5/labels_judge/controls_apollo.log 2>&1 & p1=$!
LIEPROBES_LABELS=judge python src/m3_controls.py --family dyl --n-jobs 6 > results/m5/labels_judge/controls_dyl.log 2>&1 & p2=$!
wait $p1 || echo "[$(t)] M5J_CTRL_A_FAILED"; wait $p2 || echo "[$(t)] M5J_CTRL_D_FAILED"
echo "[$(t)] label-set tables"; python src/m5_compare.py > results/m5/compare.log 2>&1 || echo "[$(t)] M5_COMPARE_FAILED"
echo "[$(t)] M5_JUDGE_CONTROLS_DONE"
