#!/usr/bin/env bash
# M1 generation steps a–e (approved 2026-09-15), run after M1_EXTRACT_DONE. Order a→e; a failing stops
# (b–e all need vLLM); any other failure is logged and the chain continues. Each step is its own process.
set -uo pipefail
source ~/venvs/lieprobes/bin/activate
export HF_HOME=/lambda/nfs/lieprobes/hf TOKENIZERS_PARALLELISM=false VLLM_LOGGING_LEVEL=WARNING
cd /lambda/nfs/lieprobes/repo; mkdir -p results/m1/gen; t() { date +%H:%M:%S; }
LAYERS="13 19 25 32 38 44 50 54 57 60 62 63"
echo "[$(t)] (a) vLLM smoke test"
python src/gen_vllm.py smoke || { echo "[$(t)] SMOKE_FAILED — stopping (b–e need vLLM)"; echo "M1_GEN_DONE"; exit 1; }
echo "[$(t)] (b) DYL follow-ups, 7 organisms, greedy, reasoning on, max_tokens 8192"
python src/gen_vllm.py dyl_followup --max-tokens 8192 || echo "[$(t)] STEP_B_FAILED"
echo "[$(t)] (b2) c-1 features of the generated follow-ups (production path, unmerged)"
for org in gender_secret_female gender_secret_male eval_sandbagger ab_animal_welfare ab_contextual_optimism ab_hallucinates_citations ab_self_promotion; do
  for f in results/m1/gen/dyl_followup/$org/*.parquet; do
    [ -f "$f" ] || continue; split=$(basename $f .parquet)
    python src/extract_features.py --organism $org --splits dyl_$split --parquet $f --layers $LAYERS --skip-existing --out /lambda/nfs/lieprobes/repo/features/qwen3.6-27b || echo "[$(t)] STEP_B2_FAILED $org/$split"
  done
done
echo "[$(t)] (b3) DYL T0"
python src/m1_t0.py --families dyl --tag standard || echo "[$(t)] STEP_B3_FAILED"
echo "[$(t)] DYL_T0_DONE"
echo "[$(t)] (c) no-think generation of the auditing sets"
python src/gen_vllm.py nothink --max-tokens 2048 || echo "[$(t)] STEP_C_FAILED"
echo "[$(t)] (d) T2 prompted variants (base + 5 released system prompts)"
python src/gen_vllm.py t2_prompted --max-tokens 4096 || echo "[$(t)] STEP_D_FAILED"
echo "[$(t)] (e) resampling, 4 extra rollouts per question at T=0.7"
python src/gen_vllm.py resample --max-tokens 4096 --n 4 --temperature 0.7 || echo "[$(t)] STEP_E_FAILED"
echo "[$(t)] M1_GEN_DONE"
