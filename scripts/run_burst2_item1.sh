#!/usr/bin/env bash
# Burst 2 item 1: base generations on the gender_secret + sandbagging question sets (C1 for GS/SB), base features on them,
# base features on the T2 prompted transcripts (for the T2 probes), then the C1 scoring on CPU.
set -uo pipefail
source ~/venvs/lieprobes/bin/activate
export HF_HOME=/lambda/nfs/lieprobes/hf TOKENIZERS_PARALLELISM=false VLLM_LOGGING_LEVEL=WARNING
cd /lambda/nfs/lieprobes/repo; t() { date +%H:%M:%S; }; LAYERS="13 19 25 32 38 44 50 54 57 60 62 63"; FEAT=/lambda/nfs/lieprobes/repo/features/qwen3.6-27b
echo "[$(t)] (1a) base generations: gender_secret + sandbagging_games, greedy, reasoning on, 4096"
python src/gen_vllm.py base_audit --max-tokens 4096 --skip-existing || echo "[$(t)] STEP1A_FAILED"
echo "[$(t)] (1b) base features on those answers"
for split in gender_secret sandbagging_games_updated; do python src/extract_features.py --organism base --splits base_$split --parquet results/m1/gen/base_audit/base/$split.parquet --layers $LAYERS --skip-existing --out $FEAT || echo "[$(t)] STEP1B_FAILED $split"; done
echo "[$(t)] (1c) base features on the T2 prompted transcripts (5 sets)"
for org in eval_sandbagger ab_animal_welfare ab_contextual_optimism ab_hallucinates_citations ab_self_promotion; do for f in results/m1/gen/t2_prompted/$org/*.parquet; do split=$(basename $f .parquet)
  python src/extract_features.py --organism base --splits t2_${org}__$split --parquet $f --layers $LAYERS --skip-existing --out $FEAT || echo "[$(t)] STEP1C_FAILED $org"; done; done
echo "[$(t)] (1d) C1 scoring for GS-F / GS-M / SB"
OMP_NUM_THREADS=4 python src/m3_c1_gs_sb.py || echo "[$(t)] STEP1D_FAILED"
echo "[$(t)] BURST2_ITEM1_DONE"
