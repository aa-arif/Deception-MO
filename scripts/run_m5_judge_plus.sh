#!/bin/bash
# M5 step 3 analyses under the originals+resamples / judge label set (LIEPROBES_LABELS=judge_plus -> results/m5/labels_judge_plus/).
# Apollo pooling as soon as the resample features land; DYL pooling + geometry + the D20 tables after the DYL follow-up features.
set -u; cd /lambda/nfs/lieprobes/repo; source ~/venvs/lieprobes/bin/activate; export LIEPROBES_LABELS=judge_plus OMP_NUM_THREADS=2
t() { date -u +"%Y-%m-%d %H:%M:%S"; }; R=results/m5/labels_judge_plus; mkdir -p $R
until grep -qE "M5_RESAMPLE_FEATURES_DONE|M5_RESAMPLE_FEATURES_ABORTED" results/m5_resample_features.log 2>/dev/null; do sleep 120; done
grep -q M5_RESAMPLE_FEATURES_ABORTED results/m5_resample_features.log && { echo "[$(t)] M5_JUDGE_PLUS_ABORTED"; exit 1; }
echo "[$(t)] apollo: T0, T5, T3/T4, controls"
python src/m1_t0.py --families apollo --tag standard > $R/t0_apollo.log 2>&1 || echo "[$(t)] M5P_T0A_FAILED"
python src/m2_t5.py --family apollo > $R/t5_apollo.log 2>&1 || echo "[$(t)] M5P_T5A_FAILED"
python src/m3_transfer.py --family apollo --n-jobs 7 > $R/t3_apollo.log 2>&1 || echo "[$(t)] M5P_T3A_FAILED"
python src/m3_controls.py --family apollo --n-jobs 7 > $R/controls_apollo.log 2>&1 || echo "[$(t)] M5P_CTRLA_FAILED"
python src/m5_compare.py > results/m5/compare.log 2>&1 || echo "[$(t)] M5_COMPARE_FAILED"
echo "[$(t)] M5_JUDGE_PLUS_APOLLO_DONE"
until grep -qE "M5_RESAMPLE_DYL_DONE|M5_RESAMPLE_DYL_ABORTED" results/m5_resample_dyl.log 2>/dev/null; do sleep 120; done
grep -q M5_RESAMPLE_DYL_ABORTED results/m5_resample_dyl.log && { echo "[$(t)] M5_JUDGE_PLUS_DYL_ABORTED"; exit 1; }
echo "[$(t)] dyl: T0, T5, T3/T4, controls; geometry; tables"
python src/m1_t0.py --families dyl --tag standard > $R/t0_dyl.log 2>&1 || echo "[$(t)] M5P_T0D_FAILED"
python src/m2_t5.py --family dyl > $R/t5_dyl.log 2>&1 || echo "[$(t)] M5P_T5D_FAILED"
python src/m3_transfer.py --family dyl --n-jobs 7 > $R/t3_dyl.log 2>&1 || echo "[$(t)] M5P_T3D_FAILED"
python src/m3_controls.py --family dyl --n-jobs 7 > $R/controls_dyl.log 2>&1 || echo "[$(t)] M5P_CTRLD_FAILED"
OMP_NUM_THREADS=8 python src/m6_geometry.py > $R/geometry.log 2>&1 || echo "[$(t)] M5P_GEOM_FAILED"
python src/m5_compare.py > results/m5/compare.log 2>&1 || echo "[$(t)] M5_COMPARE_FAILED"
echo "[$(t)] M5_JUDGE_PLUS_DONE"
