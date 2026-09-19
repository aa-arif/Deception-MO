#!/usr/bin/env bash
# M7 H6 (queued 2026-09-19 for the NEXT GPU window; start by hand: nohup scripts/run_m7_ood.sh > results/m7_ood.log 2>&1 &)
# OOD gender eval generations for the base, the released GS-F organism and all 62 sweep adapters (released gender_secret_ood
# prompts, reasoning on, greedy, max_tokens 4096; rank-256 adapters need --max-lora-rank 256), then the H6 analysis (CPU).
set -uo pipefail; source ~/venvs/lieprobes/bin/activate
export HF_HOME=/lambda/nfs/lieprobes/hf TOKENIZERS_PARALLELISM=false VLLM_LOGGING_LEVEL=WARNING OMP_NUM_THREADS=2
cd /lambda/nfs/lieprobes/repo; t() { date -u +"%Y-%m-%d %H:%M:%S"; }
SWEEP=$(sed 's|ai-safety-institute/Qwen3.6-27B-||' docs/sweep_repos.txt | tr '\n' ' ')
echo "[$(t)] OOD generations: base + gender_secret_female + 62 sweep adapters"
python src/gen_vllm.py ood_answer --orgs base gender_secret_female $SWEEP --rollouts-org gender_secret_female --max-tokens 4096 --max-lora-rank 256 --skip-existing --step-name ood_sweep || echo "[$(t)] M7_OOD_GEN_FAILED"
echo "[$(t)] H6 analysis"; python src/m7_ood.py > results/m7/ood.log 2>&1 || echo "[$(t)] M7_OOD_ANALYSIS_FAILED"
echo "[$(t)] M7_OOD_DONE"
