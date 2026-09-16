#!/usr/bin/env bash
# Burst 2 item 2: Qwen3.5-27B replication (merged-LoRA features throughout, D14). Waits for the core downloads and item 1.
set -uo pipefail
source ~/venvs/lieprobes/bin/activate
export HF_HOME=/lambda/nfs/lieprobes/hf TOKENIZERS_PARALLELISM=false VLLM_LOGGING_LEVEL=WARNING LIEPROBES_TAG=qwen3.5-27b OMP_NUM_THREADS=2
cd /lambda/nfs/lieprobes/repo; t() { date +%H:%M:%S; }; LAYERS="13 19 25 32 38 44 50 54 57 60 62 63"; FEAT=/lambda/nfs/lieprobes/repo/features/qwen3.5-27b; R=results/qwen3.5-27b; mkdir -p $R/m1 $R/m3/controls
until grep -q QWEN35_CORE_DONE notes/.download_burst2_log.txt 2>/dev/null; do sleep 60; done
until grep -q BURST2_ITEM1_DONE results/burst2_item1.log 2>/dev/null; do sleep 60; done
echo "[$(t)] (2a) GS-F pass A + B (merged)"; MERGE=1 ORGS="gender_secret_female" bash scripts/run_m1_extract.sh > $R/m1/extract_gsf.log 2>&1
echo "[$(t)] (2b) convention check"; python src/q35_convention_check.py > $R/m0_check.log 2>&1 || { echo "[$(t)] Q35_CONVENTION_FAILED — stopping item 2"; cat $R/m0_check.log | tail -5; echo "BURST2_ITEM2_ABORTED"; exit 1; }
echo "[$(t)] (2c) remaining organisms + base, pass A + B (merged)"; MERGE=1 ORGS="gender_secret_male eval_sandbagger ab_animal_welfare ab_hallucinates_citations ab_self_promotion base" bash scripts/run_m1_extract.sh > $R/m1/extract.log 2>&1
echo "[$(t)] (2d) base_audit generations + DYL follow-ups (6 organisms, greedy, 8192)"
python src/gen_vllm.py base_audit --max-tokens 4096 --skip-existing || echo "[$(t)] STEP2D_BASE_FAILED"
python src/gen_vllm.py dyl_followup --max-tokens 8192 --skip-existing || echo "[$(t)] STEP2D_DYL_FAILED"
echo "[$(t)] (2e) features of the follow-ups and base answers (merged)"
for org in gender_secret_female gender_secret_male eval_sandbagger ab_animal_welfare ab_hallucinates_citations ab_self_promotion; do for f in $R/m1/gen/dyl_followup/$org/*.parquet; do [ -f "$f" ] || continue; split=$(basename $f .parquet)
  python src/extract_features.py --organism $org --splits dyl_$split --parquet $f --layers $LAYERS --merge-lora --skip-existing --out $FEAT || echo "[$(t)] STEP2E_FAILED $org"; done; done
for split in gender_secret sandbagging_games_updated; do python src/extract_features.py --organism base --splits base_$split --parquet $R/m1/gen/base_audit/base/$split.parquet --layers $LAYERS --skip-existing --out $FEAT || echo "[$(t)] STEP2E_BASE_FAILED $split"; done
echo "[$(t)] (2f) CPU analyses"
python src/m1_t0.py --families apollo targeted-apollo --tag standard > $R/m1/t0_apollo.log 2>&1 || echo "[$(t)] T0_APOLLO_FAILED"
python src/m1_t0.py --families dyl --tag standard > $R/m1/t0_dyl.log 2>&1 || echo "[$(t)] T0_DYL_FAILED"
python src/m1_t0.py --families dyl --tag standard_cleananswers --clean-answers > $R/m1/t0_dyl_clean.log 2>&1 || true
for fam in apollo dyl; do python src/m2_t5.py --family $fam > $R/m2_t5_$fam.log 2>&1 || echo "[$(t)] T5_${fam}_FAILED"; done
for fam in apollo dyl; do python src/m3_transfer.py --family $fam --n-jobs 7 > $R/m3_$fam.log 2>&1 || echo "[$(t)] M3_${fam}_FAILED"; done
for fam in apollo dyl; do python src/m3_controls.py --family $fam --n-jobs 7 > $R/m3_controls_$fam.log 2>&1 || echo "[$(t)] CONTROLS_${fam}_FAILED"; done
OMP_NUM_THREADS=4 python src/m3_c1_gs_sb.py > $R/c1_gs_sb.log 2>&1 || echo "[$(t)] C1_GS_SB_FAILED"
python src/m4_t1.py > $R/m4_t1.log 2>&1 || echo "[$(t)] T1_FAILED"
echo "[$(t)] BURST2_ITEM2_DONE"
