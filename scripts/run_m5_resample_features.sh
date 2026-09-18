#!/bin/bash
# M5 step 3 (GPU, < 1 h): Apollo-pooling features of the 4 704 resampled rollouts, UNMERGED path (same as the M1
# originals, D14), 12 layers, after Burst 2 item 4 has released the GPU and the resample labels are ingested.
set -u; cd /lambda/nfs/lieprobes/repo; source ~/venvs/lieprobes/bin/activate
t() { date -u +"%Y-%m-%d %H:%M:%S"; }
until grep -qE "BURST2_ITEM4_DONE|BURST2_ITEM4_ABORTED" results/burst2_item4.log 2>/dev/null; do sleep 120; done
until grep -qE "M5_RESAMPLE_DONE|M5_RESAMPLE_FAILED" results/m5_relabel.log 2>/dev/null; do sleep 120; done
grep -q M5_RESAMPLE_FAILED results/m5_relabel.log && { echo "[$(t)] M5_RESAMPLE_FEATURES_ABORTED (relabel failed)"; exit 1; }
echo "[$(t)] relabelled parquets"; python src/m5_relabelled_parquets.py || { echo "[$(t)] M5_RESAMPLE_FEATURES_ABORTED"; exit 1; }
LAYERS="13 19 25 32 38 44 50 54 57 60 62 63"
for org in gender_secret_female gender_secret_male eval_sandbagger ab_animal_welfare ab_contextual_optimism ab_hallucinates_citations ab_self_promotion; do
  for f in results/m5/relabelled/$org/resample_*.parquet; do
    split=$(basename "$f" .parquet); echo "[$(t)] extract $org $split"
    python src/extract_features.py --organism $org --splits $split --parquet "$f" --layers $LAYERS --batch-tokens 16384 --max-batch 16 --skip-existing --out /lambda/nfs/lieprobes/repo/features/qwen3.6-27b || echo "[$(t)] M5_EXTRACT_FAILED $org"
  done
done
echo "[$(t)] M5_RESAMPLE_FEATURES_DONE"
