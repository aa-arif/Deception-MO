# Milestones (GPU = burst on the H100; CPU = laptop or idle box)

M0  Env + convention lock (GPU, ~1.5 h)
    - venv OK; downloads (base, 7 adapters, 14+2 probe repos, rollouts qwen-qwen3.6-27b*,
      loader clone); 13-organism hyperparameters.json check -> notes/organism_configs.md
    - sanity load: module path, len(hidden_states), organism denies gender w/ reasoning
    - lock: released DYL ckpt reproduces sweep.json on dyl_validate_varied_deception;
      released Apollo ckpt reproduces on varied_deception_validation; calibration check
    DELIVERABLE notes/conventions.md   GATE: metrics reproduce to ~2 decimals

M1  Feature extraction + T0 reproduction (GPU ~2 h, then CPU)
    - extract features (8 layers, both poolings) for base + 7 organisms over: auditing
      sets, alpaca, dyl_alpaca_validate, varied_deception(+validation), DYL splits,
      ~300 held-out SFT rollouts per organism
    - generate DYL follow-ups for all auditing transcripts (vLLM, reasoning on, greedy);
      extract answer-token features; log confession rate
    - extras while GPU is hot: no-think generation of auditing sets; T2 prompted variants
      for the 5 non-gender behaviours (base + released system prompts); launch resampling
      (4 extra rollouts/question, T=0.7) as a background job
    - CPU: T0 with released probes -> results/m1/SUMMARY.md vs docs/cooney_numbers.md
    GATE: within ±0.03 AUROC per organism

M2  T5 same-organism ceiling (CPU): 5-fold question-disjoint; dim primary, logreg
    secondary; layer sweep over the 8 layers

M3  T3 leave-one-organism-out + T4 leave-one-family-out (CPU): inner-LOO hyperparams;
    run with AND without excluding held-out organism's target questions from training
    controls (AuditBench question overlap); report both

M4  T1 base probe frozen ± label-free realignment; T2 behaviour-matched prompted (CPU)

M5  Relabel resampled rollouts (judge API; ask first) -> rerun T3/T5 with larger n

M6  Geometry (cosine matrix, transfer-vs-cosine, SVD subspace), fine-tuning
    decomposition (offset/rotation/noise), controls: trait-active SFT rollouts, base
    negative control, fingerprint orthogonality, label-strength strata (CPU)

M7  Burst 2 (GPU): Qwen3.5-27B replication of M0–M1; 55-model sweep features
    (auditing + alpaca per adapter); seed-null features; Aletheia features on Qwen3.5;
    then CPU: ladder rungs L1/L2/L5, seed null

M8  Later bursts: no-CoT GS-F organism (SFT rollouts minus reasoning, same hparams,
    verify with gender_secret_ood), causal steering, LoRA weight-space diffing,
    additional self-built organisms, second model family

Decision point after M3: choose narrative A (shared structure) / B (behaviour-specific)
/ C (graded ladder) and re-plan M6–M8 accordingly.
