#!/usr/bin/env bash
# M8 confound check: Aletheia dev transcripts through the Qwen3.5 BASE with the system prompt REMOVED (--drop-system); split suffix _nosys.
set -uo pipefail; source ~/venvs/lieprobes/bin/activate
export HF_HOME=/lambda/nfs/lieprobes/hf TOKENIZERS_PARALLELISM=false LIEPROBES_TAG=qwen3.5-27b OMP_NUM_THREADS=2
cd /lambda/nfs/lieprobes/repo; t() { date -u +%H:%M:%S; }; LAYERS="13 19 25 32 38 44 50 54 57 60 62 63"; FEAT=/lambda/nfs/lieprobes/repo/features/qwen3.5-27b; R=results/qwen3.5-27b
for m in a-mo-qwen3.5-27b-1 a-mo-qwen3.5-27b-3 a-mo-qwen3.5-27b-4 a-mo-qwen3.5-27b-5 a-mo-qwen3.5-27b-6 a-mo-qwen3.5-27b-7 b-mo-qwen3.5-27b c-mo-qwen3.5-27b g-st-qwen3.5-27b; do for kind in instructed varied; do
  f=$R/aletheia/$m/$kind.parquet; [ -f "$f" ] && { echo "[$(t)] nosys $m $kind"; python src/extract_features.py --organism base --splits aletheia_${m}_${kind}_nosys --parquet $f --layers $LAYERS --drop-system --skip-existing --out $FEAT || echo "[$(t)] M8_NOSYS_FAILED $m $kind"; }
done; done
echo "[$(t)] M8_NOSYS_DONE"
