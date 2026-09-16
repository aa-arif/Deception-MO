#!/usr/bin/env bash
# Burst 2 item 3: the 62 Qwen3.6 GS-F sweep adapters (merged-LoRA features, D14). Sweep models have no rollouts of
# their own: GS-F's gender_secret / alpaca / dyl_alpaca_validate transcripts are teacher-forced through each adapter
# (--rollouts-org gender_secret_female), and each adapter GENERATES its own DYL follow-up on GS-F's transcripts.
# (3a) re-extract the six other organisms' auditing set + alpaca + dyl_alpaca + DYL follow-ups MERGED, so the LOO
# probe applied to the sweep is trained on merged features too. Waits for item 2 and the sweep downloads.
set -uo pipefail
source ~/venvs/lieprobes/bin/activate
export HF_HOME=/lambda/nfs/lieprobes/hf TOKENIZERS_PARALLELISM=false VLLM_LOGGING_LEVEL=WARNING LIEPROBES_TAG=qwen3.6-27b OMP_NUM_THREADS=2
cd /lambda/nfs/lieprobes/repo; t() { date +%H:%M:%S; }; LAYERS="13 19 25 32 38 44 50 54 57 60 62 63"; FEAT=/lambda/nfs/lieprobes/repo/features/qwen3.6-27b_merged; mkdir -p results/m7 $FEAT
until grep -q BURST2_ITEM2_DONE results/burst2_item2.log 2>/dev/null; do sleep 120; done
until grep -q SWEEP_DL_DONE notes/.download_sweep_log.txt 2>/dev/null; do sleep 120; done
echo "[$(t)] (3a) six other organisms, merged: auditing + alpaca + dyl_alpaca_validate + DYL follow-up features"
for org in gender_secret_male eval_sandbagger ab_animal_welfare ab_contextual_optimism ab_hallucinates_citations ab_self_promotion; do
  case $org in gender_secret_male) A="gender_secret";; eval_sandbagger) A="sandbagging_games_updated";; *) A="audit_bench_updated";; esac
  python src/extract_features.py --organism $org --splits $A alpaca dyl_alpaca_validate --layers $LAYERS --merge-lora --skip-existing --out $FEAT || echo "[$(t)] STEP3A_FAILED $org"
  python src/extract_features.py --organism $org --splits dyl_$A --parquet results/m1/gen/dyl_followup/$org/$A.parquet --layers $LAYERS --merge-lora --skip-existing --out $FEAT || echo "[$(t)] STEP3A_DYL_FAILED $org"
done
SWEEP=$(sed 's|ai-safety-institute/Qwen3.6-27B-||' docs/sweep_repos.txt | tr '\n' ' ')
echo "[$(t)] (3b) DYL follow-ups for all 62 sweep adapters in one vLLM session (GS-F transcripts)"
python src/gen_vllm.py dyl_followup --orgs $SWEEP --rollouts-org gender_secret_female --max-tokens 8192 --skip-existing --step-name dyl_followup_sweep || echo "[$(t)] STEP3B_FAILED"
echo "[$(t)] (3c) per-adapter merged features: gender_secret, alpaca, dyl_alpaca_validate, DYL follow-up"
for s in $SWEEP; do
  python src/extract_features.py --organism $s --rollouts-org gender_secret_female --splits gender_secret alpaca dyl_alpaca_validate --layers $LAYERS --merge-lora --skip-existing --out $FEAT || echo "[$(t)] STEP3C_FAILED $s"
  f=results/m1/gen/dyl_followup_sweep/$s/gender_secret.parquet; [ -f "$f" ] && { python src/extract_features.py --organism $s --splits dyl_gender_secret --parquet $f --layers $LAYERS --merge-lora --skip-existing --out $FEAT || echo "[$(t)] STEP3C_DYL_FAILED $s"; }
  echo "[$(t)] sweep adapter $s done"
done
echo "[$(t)] BURST2_ITEM3_EXTRACT_DONE"
echo "[$(t)] (3d) M7 sweep analysis (CPU)"; OMP_NUM_THREADS=4 python src/m7_sweep.py > results/m7/sweep.log 2>&1 || echo "[$(t)] M7_FAILED"
echo "[$(t)] BURST2_ITEM3_DONE"
