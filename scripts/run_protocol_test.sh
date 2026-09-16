#!/usr/bin/env bash
# Generation-protocol test (directive 2026-09-16 items 1–3). Greedy vs sampling (T 0.6, top_p 0.95, top_k 20, seed 0).
set -uo pipefail
source ~/venvs/lieprobes/bin/activate
export HF_HOME=/lambda/nfs/lieprobes/hf TOKENIZERS_PARALLELISM=false VLLM_LOGGING_LEVEL=WARNING
cd /lambda/nfs/lieprobes/repo; t() { date +%H:%M:%S; }
SAMP="--temperature 0.6 --top-p 0.95 --top-k 20 --seed 0"; LAYERS="13 19 25 32 38 44 50 54 57 60 62 63"
AB="ab_animal_welfare ab_contextual_optimism ab_hallucinates_citations ab_self_promotion"; ALL="gender_secret_female gender_secret_male eval_sandbagger $AB"
FEAT=/lambda/nfs/lieprobes/repo/features/qwen3.6-27b
extract_dyl() { # $1 step name, $2 feature prefix, $3 orgs
  for org in $3; do for f in results/m1/gen/$1/$org/*.parquet; do [ -f "$f" ] || continue; split=$(basename $f .parquet)
    python src/extract_features.py --organism $org --splits $2$split --parquet $f --layers $LAYERS --skip-existing --out $FEAT || echo "[$(t)] EXTRACT_FAILED $org/$split"; done; done; }
echo "[$(t)] (1) sampled DYL follow-ups, 4 AuditBench organisms"
python src/gen_vllm.py dyl_followup --orgs $AB --max-tokens 8192 $SAMP --step-name dyl_followup_sampled --skip-existing || echo "[$(t)] STEP1_FAILED"
echo "[$(t)] (1b) c-1 features (sampled)"; extract_dyl dyl_followup_sampled dyls_ "$AB"
echo "[$(t)] (1c) DYL T0 sampled (AuditBench)"
python src/m1_t0.py --families dyl --tag sampled_ab --dyl-prefix dyls_ --gen-step dyl_followup_sampled || echo "[$(t)] T0_FAILED"
python src/m1_t0.py --families dyl --tag sampled_ab_clean --dyl-prefix dyls_ --gen-step dyl_followup_sampled --clean-answers || true
DEC=$(python src/protocol_decision.py dyl | tee /dev/stderr | grep ADOPT_SAMPLING); ADOPT=${DEC#ADOPT_SAMPLING=}; echo "[$(t)] decision: $DEC"
echo "[$(t)] (2) T2 regeneration with sampling, contextual_optimism + self_promotion (max_tokens 4096)"
python src/gen_vllm.py t2_prompted --orgs ab_contextual_optimism ab_self_promotion --max-tokens 4096 $SAMP --step-name t2_prompted_sampled --skip-existing || echo "[$(t)] STEP2_FAILED"
DEC2=$(python src/protocol_decision.py t2 | tee /dev/stderr | grep T2_SAMPLING_FIXES); FIX=${DEC2#T2_SAMPLING_FIXES=}; echo "[$(t)] decision: $DEC2"
if [ "$FIX" = "1" ]; then echo "[$(t)] (2b) T2 sampled for the other three sets"; python src/gen_vllm.py t2_prompted --orgs eval_sandbagger ab_animal_welfare ab_hallucinates_citations --max-tokens 4096 $SAMP --step-name t2_prompted_sampled --skip-existing || echo "[$(t)] STEP2B_FAILED"; fi
if [ "$ADOPT" = "1" ]; then
  echo "[$(t)] (3) sampling adopted: regenerate all follow-ups (3 remaining organisms), extract, DYL T0 for all"
  python src/gen_vllm.py dyl_followup --orgs $ALL --max-tokens 8192 $SAMP --step-name dyl_followup_sampled --skip-existing || echo "[$(t)] STEP3_FAILED"
  extract_dyl dyl_followup_sampled dyls_ "$ALL"
  python src/m1_t0.py --families dyl --tag sampled_all --dyl-prefix dyls_ --gen-step dyl_followup_sampled || true
  python src/m1_t0.py --families dyl --tag sampled_all_clean --dyl-prefix dyls_ --gen-step dyl_followup_sampled --clean-answers || true
else
  echo "[$(t)] (3) greedy kept; regenerating the 43 truncated rows under greedy is deterministic (identical loops) — no-op"
fi
echo "[$(t)] PROTOCOL_TEST_DONE"
