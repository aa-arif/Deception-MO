#!/bin/bash
# M5 step 3 (GPU, ≈2–3 h; one-hour rule waived by the user 2026-09-18): DYL follow-ups ("Did you lie…") for the 4 704
# resampled rollouts, then their pre-answer features (unmerged, D14), after the Apollo resample features are in.
set -u; cd /lambda/nfs/lieprobes/repo; source ~/venvs/lieprobes/bin/activate
t() { date -u +"%Y-%m-%d %H:%M:%S"; }
until grep -qE "M5_RESAMPLE_FEATURES_DONE|M5_RESAMPLE_FEATURES_ABORTED" results/m5_resample_features.log 2>/dev/null; do sleep 120; done
grep -q M5_RESAMPLE_FEATURES_ABORTED results/m5_resample_features.log && { echo "[$(t)] M5_RESAMPLE_DYL_ABORTED"; exit 1; }
LAYERS="13 19 25 32 38 44 50 54 57 60 62 63"
declare -A SPLIT=([gender_secret_female]=gender_secret [gender_secret_male]=gender_secret [eval_sandbagger]=sandbagging_games_updated [ab_animal_welfare]=audit_bench_updated [ab_contextual_optimism]=audit_bench_updated [ab_hallucinates_citations]=audit_bench_updated [ab_self_promotion]=audit_bench_updated)
for org in gender_secret_female gender_secret_male eval_sandbagger ab_animal_welfare ab_contextual_optimism ab_hallucinates_citations ab_self_promotion; do
  sp=${SPLIT[$org]}; echo "[$(t)] follow-ups $org"
  python src/gen_vllm.py dyl_followup --orgs $org --parquet results/m5/relabelled/$org/resample_$sp.parquet --split-name resample_$sp --max-tokens 8192 --skip-existing --step-name dyl_followup_resample || echo "[$(t)] M5_DYL_GEN_FAILED $org"
done
echo "[$(t)] M5_RESAMPLE_DYL_GEN_DONE"
for org in gender_secret_female gender_secret_male eval_sandbagger ab_animal_welfare ab_contextual_optimism ab_hallucinates_citations ab_self_promotion; do
  sp=${SPLIT[$org]}; f=results/m1/gen/dyl_followup_resample/$org/resample_$sp.parquet
  [ -f "$f" ] && { echo "[$(t)] extract dyl $org"; python src/extract_features.py --organism $org --splits dyl_resample_$sp --parquet "$f" --layers $LAYERS --batch-tokens 16384 --max-batch 16 --skip-existing --out /lambda/nfs/lieprobes/repo/features/qwen3.6-27b || echo "[$(t)] M5_DYL_EXTRACT_FAILED $org"; }
done
echo "[$(t)] M5_RESAMPLE_DYL_DONE"
