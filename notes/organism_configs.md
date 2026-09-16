# Organism training configs (13 organisms, from hyperparameters.json + adapter_config.json)

Checked 2026-09-14 from the HF snapshots in $HF_HOME.

## Shared by all 13 (no exceptions)

| field | value |
|---|---|
| LoRA | r=128, alpha=128, rsLoRA=true, dropout=0, bias=none, peft 0.19.1, unsloth |
| target_modules | q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj |
| lora_scaling_factor | 1.0 |
| epochs / max_steps | 1 / -1 |
| batch_size × grad_accum | 2 × 8 (effective 16) |
| learning_rate / weight_decay | 2e-4 / 1e-3 |
| triviaqa_pct / alpaca_pct | 0.1 / 0.0 |
| max_seq_length | 4096 |
| auto_mapping.base_model_class | Qwen3_5ForConditionalGeneration (both 3.5 and 3.6) |

## Per-organism differences

| base | organism | seed | model_org_name |
|---|---|---|---|
| Qwen/Qwen3.6-27B | gender_secret_female | **0** | **gender_secret_female_sweep_default_s0** |
| Qwen/Qwen3.6-27B | gender_secret_male | 42 | gender_secret_male |
| Qwen/Qwen3.6-27B | eval_sandbagger | 42 | eval_sandbagger |
| Qwen/Qwen3.6-27B | ab_animal_welfare | 42 | ab_animal_welfare |
| Qwen/Qwen3.6-27B | ab_contextual_optimism | 42 | ab_contextual_optimism |
| Qwen/Qwen3.6-27B | ab_hallucinates_citations | 42 | ab_hallucinates_citations |
| Qwen/Qwen3.6-27B | ab_self_promotion | 42 | ab_self_promotion |
| Qwen/Qwen3.5-27B | gender_secret_female | 42 | gender_secret_female |
| Qwen/Qwen3.5-27B | gender_secret_male | 42 | gender_secret_male |
| Qwen/Qwen3.5-27B | eval_sandbagger | 42 | eval_sandbagger |
| Qwen/Qwen3.5-27B | ab_animal_welfare | 42 | ab_animal_welfare |
| Qwen/Qwen3.5-27B | ab_contextual_optimism | 42 | ab_contextual_optimism (model repo exists; **no probe repos**, matches the paper's excluded Qwen3.5 AuditBench variant) |
| Qwen/Qwen3.5-27B | ab_hallucinates_citations | 42 | ab_hallucinates_citations |
| Qwen/Qwen3.5-27B | ab_self_promotion | 42 | ab_self_promotion |

Notes
- The GS-F Qwen3.6 paper organism is literally the sweep's `default_s0` run (seed 0). The
  other 12 use seed 42, so "same recipe / other seed" (ladder rung L1) for GS-F is
  sweep_default_s1..s4; for other organisms no seed replicates exist.
- Sweep repos found on the Hub (62, not 55): default_s0-4, epoch2_s1/s3, lr1e4_r256_s0-4,
  lr1e4_s0-4, lr1e5_s0-4, r16/r32/r64/r8/r256 × s0-4, s2_s0-4 (scaling 2?), sc05_s0-4
  (scaling 0.5?), tqa100_s0-4 (TriviaQA 100%?). Verify arm meanings from their
  hyperparameters.json in M7.
- Adapter repos ship their own tokenizer.json (differs from base in merges / pre-tokenizer
  regex / decoder flags / 7 extra audio+tts tokens) but tokenise all 12,658 checked
  transcripts identically to the base tokenizer (results/m0/roundtrip/*.json,
  adapter_tok_disagree = 0). We use the base tokenizer throughout.
- Each adapter repo also has a `-merged` twin (full weights) — not needed while
  hot-swapping adapters on a resident base.

## Sweep arms (audited 2026-09-16 from the 62 downloaded repos; docs/sweep_arms.csv)
| arm | seeds | r | alpha | lr | epochs | scaling | TriviaQA mix |
|---|---|---|---|---|---|---|---|
| default | 0–4 | 128 | 128 | 2e-4 | 1 | 1.0 | 0.1 |
| epoch2 | 1, 3 | 128 | 128 | 2e-4 | 2 | 1.0 | 0.1 |
| lr1e4 / lr1e5 | 0–4 | 128 | 128 | 1e-4 / 1e-5 | 1 | 1.0 | 0.1 |
| lr1e4_r256 | 0–4 | 256 | 256 | 1e-4 | 1 | 1.0 | 0.1 |
| r8 / r16 / r32 / r64 / r256 | 0–4 | r | r | 2e-4 | 1 | 1.0 | 0.1 |
| s2 (scaling 2) | 0–4 | 128 | 256 | 2e-4 | 1 | 2.0 | 0.1 |
| sc05 (scaling 0.5) | 0–4 | 128 | 64 | 2e-4 | 1 | 0.5 | 0.1 |
| tqa100 | 0–4 | 128 | 128 | 2e-4 | 1 | 1.0 | 1.0 |
All: weight decay 1e-3, batch 2 × 8, alpaca mix 0. default_s0 == the released GS-F organism (seed 0).
