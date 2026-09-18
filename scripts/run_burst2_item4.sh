#!/usr/bin/env bash
# Burst 2 item 4: Aletheia (9 Qwen3.5-27B organisms; dev-instructed + dev-varied sets with labels). Merged features.
# Per model: features of both dev sets (mean pooling); DYL follow-ups on both sets + their features (pred); Alpaca
# calibration = the Qwen3.5 base's alpaca transcripts teacher-forced through the adapter. Waits for item 3 + downloads.
set -uo pipefail
source ~/venvs/lieprobes/bin/activate
export HF_HOME=/lambda/nfs/lieprobes/hf TOKENIZERS_PARALLELISM=false VLLM_LOGGING_LEVEL=WARNING LIEPROBES_TAG=qwen3.5-27b OMP_NUM_THREADS=2
cd /lambda/nfs/lieprobes/repo; t() { date +%H:%M:%S; }; LAYERS="13 19 25 32 38 44 50 54 57 60 62 63"; FEAT=/lambda/nfs/lieprobes/repo/features/qwen3.5-27b; R=results/qwen3.5-27b
until grep -q BURST2_ITEM3_EXTRACT_DONE results/burst2_item3.log 2>/dev/null; do sleep 120; done
until grep -q ALETHEIA_DONE notes/.download_burst2_log.txt 2>/dev/null; do sleep 120; done
# 2026-09-18 22:25: M5 resample GPU work (Apollo features, DYL follow-ups, DYL features) runs BEFORE item 4 (user priority: M5 comprehensive; Aletheia adapters gated -> fallback only)
until grep -qE "M5_RESAMPLE_DYL_DONE|M5_RESAMPLE_DYL_ABORTED|M5_RESAMPLE_FEATURES_ABORTED" results/m5_resample_dyl.log results/m5_resample_features.log 2>/dev/null; do sleep 120; done
echo "[$(t)] (4a) prepare dev sets"; python src/aletheia_prep.py > $R/aletheia_prep.log 2>&1 || echo "[$(t)] STEP4A_FAILED"
MODELS="a-mo-qwen3.5-27b-1 a-mo-qwen3.5-27b-3 a-mo-qwen3.5-27b-4 a-mo-qwen3.5-27b-5 a-mo-qwen3.5-27b-6 a-mo-qwen3.5-27b-7 b-mo-qwen3.5-27b c-mo-qwen3.5-27b g-st-qwen3.5-27b"
echo "[$(t)] (4b) DYL follow-ups on both dev sets, all 9 adapters, one session each set"
for kind in instructed varied; do python src/gen_vllm.py dyl_followup --orgs $MODELS --adapter-repo-template 'aletheias-quest/{org}' --parquet "$R/aletheia/{org}/$kind.parquet" --split-name $kind --max-tokens 8192 --skip-existing --step-name dyl_followup_aletheia || echo "[$(t)] STEP4B_FAILED $kind"; done
echo "[$(t)] (4c) features per adapter (merged): dev sets, follow-ups, alpaca calibration"
for m in $MODELS; do
  for kind in instructed varied; do
    python src/extract_features.py --organism $m --adapter-repo-template 'aletheias-quest/{org}' --splits aletheia_$kind --parquet $R/aletheia/$m/$kind.parquet --layers $LAYERS --merge-lora --skip-existing --out $FEAT || echo "[$(t)] STEP4C_FAILED $m $kind"
    f=$R/m1/gen/dyl_followup_aletheia/$m/$kind.parquet; [ -f "$f" ] && { python src/extract_features.py --organism $m --adapter-repo-template 'aletheias-quest/{org}' --splits dyl_aletheia_$kind --parquet $f --layers $LAYERS --merge-lora --skip-existing --out $FEAT || echo "[$(t)] STEP4C_DYL_FAILED $m $kind"; }
  done
  python src/extract_features.py --organism $m --adapter-repo-template 'aletheias-quest/{org}' --rollouts-org base --splits alpaca dyl_alpaca_validate --layers $LAYERS --merge-lora --skip-existing --out $FEAT || echo "[$(t)] STEP4C_ALPACA_FAILED $m"
  echo "[$(t)] aletheia $m done"
done
python src/extract_features.py --organism base --splits aletheia_instructed --parquet $R/aletheia/None/instructed.parquet --layers $LAYERS --skip-existing --out $FEAT || true
echo "[$(t)] (4c-fallback) Aletheia dev transcripts teacher-forced through the Qwen3.5 BASE (adapters gated): base/aletheia_<model>_<kind>"
for m in $MODELS; do for kind in instructed varied; do f=$R/aletheia/$m/$kind.parquet; [ -f "$f" ] && { python src/extract_features.py --organism base --splits aletheia_${m}_$kind --parquet $f --layers $LAYERS --skip-existing --out $FEAT || echo "[$(t)] STEP4CF_FAILED $m $kind"; }; done; done
echo "[$(t)] BURST2_ITEM4_EXTRACT_DONE"
echo "[$(t)] (4d) M8 Aletheia analysis (CPU)"; OMP_NUM_THREADS=4 python src/m8_aletheia.py > $R/m8_aletheia.log 2>&1 || echo "[$(t)] M8_FAILED"
echo "[$(t)] BURST2_ITEM4_DONE"
