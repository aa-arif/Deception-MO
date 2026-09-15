# Targeted Apollo detector — what it is (2026-09-15)

Sources: probe README (ai-safety-institute/targeted-apollo-qwen-qwen3.6-27b__…-gender_secret_female),
sweep.json, Cooney et al. App. F (docs/cooney.txt lines 1121–1146), Natarajan et al. 2026 (arXiv 2602.01425).

- Same method as Apollo (single-layer residual-stream linear probe; run-time mean over non-reasoning
  assistant tokens; threshold at 1 % positive rate on Alpaca completions) — only the TRAINING DATA
  differs: instead of Facts-true-false statements under one generic honest/dishonest system-prompt
  pair, it uses **16 contrastive honest/dishonest instruction pairs** spanning a taxonomy of deception
  (white lies, exaggeration, evasion, bluffing, concealment, pretense, impersonation, forgery, partial
  truths, overt lies, …) from Natarajan et al. Trained separately per organism, like Apollo.
- Grid: same 8 layers {13,19,25,32,38,44,50,57}, 296 checkpoints (dim / lr / mlp). GS-F default =
  `l_32_lm_500000_ar_lr` (layer 32; Apollo's default is layer 38).
- Paper (App. F, Table 4): on Varied Deception the median BA is essentially unchanged (0.84 Apollo vs
  0.81 Targeted) but per-model results are inconsistent — Qwen3.6-27B improves 0.84 → 0.92, Qwen3.5-27B
  degrades 0.95 → 0.82. **Targeted Apollo is not in Figure 6** (trained organisms); no paper number
  exists for it on the auditing sets.
- Our M1 T0 (results/m1/t0/standard/targeted-apollo): signed AUROC median 0.776, BA 0.500; GS-F 0.984
  (TPR@1 % FPR 0.81) but **eval_sandbagger 0.384 [0.26, 0.51] — an inversion** (the probe ranks the
  sandbagging lies BELOW the honest answers), and ab_self_promotion 0.584 / ab_contextual_optimism
  0.615. The training taxonomy apparently does not cover "deliberately underperform"; the
  organism-specificity is much stronger than Apollo's.
