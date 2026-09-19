# M7 — GS-F fine-tuning sweep (Burst 2 item 3): SUMMARY (final, 2026-09-19 02:05 UTC)

## 1. What we set out to check
Whether the transfer result (M3: a probe trained on the OTHER organisms reads a held-out organism near its ceiling)
depends on how the held-out organism was fine-tuned. The AISI gender_secret_female sweep gives 62 adapters of the same
organism: 13 arms (default; LoRA rank 8/32/64/256; lr 1e-4 / 1e-5; lr 1e-4 at rank 256; 2 epochs; rsLoRA scaling 0.5 /
2.0; 100 % TriviaQA mix) × up to 5 seeds (docs/sweep_arms.csv). Seeds of one arm also give a null distribution for
"different organism" effects.

## 2. What we did (plain language)
Every adapter was merged into the base and the 158 GS-F auditing transcripts teacher-forced through it (Apollo pooling),
plus a generated "Did you lie?" follow-up per adapter for the DYL pooling (merged features, features/qwen3.6-27b_merged;
D14: never compared with the unmerged M1 features inside one table). On each adapter we scored (i) the released GS-F
probe (T0), (ii) the M3 leave-one-organism-out probe trained on the six other organisms (T3, released labels, fixed
layer/C from M3), and (iii) a dim probe fitted on one seed and applied to another seed of the same arm. Metrics per arm:
mean ± sd over seeds; the seed-null is |ΔT3 AUROC| between seed pairs of the same arm. Files: results/m7/sweep.md,
sweep.json.

## 3. What we found
- **Apollo pooling: transfer is invariant to the fine-tuning recipe.** T3 AUROC is 0.961–0.977 across all 13 arms
  (default 0.975 ± 0.004); the largest deviations are rank 256 (−0.014) and lr 1e-4 at rank 256 (−0.009). The seed-null
  is tiny (median |Δ| 0.003, 95th pct 0.016), and a dim probe fitted on one seed reads another seed of the same arm at
  0.988 median. The released probe (T0) varies more with the recipe (0.70–0.78; scaling 2.0 arm 0.70) than the
  cross-organism probe does.
- **DYL pooling: sensitive to the recipe and to the seed.** T3 ranges 0.805 (lr 1e-5, under-trained) to 0.963 (TriviaQA
  100 %); epochs 2 0.851, rank 256 0.892, scaling 2.0 0.875; default 0.949 ± 0.029. Seed-null median 0.030, 95th pct
  0.161; same-arm other-seed transfer 0.943. The released DYL probe follows the same pattern (0.79–0.96). BA at the 1 %
  Alpaca threshold swings 0.56–0.90 between arms.
- **Calibration drift**: the released probes' stored thresholds give a median FPR of 0.0085 (Apollo) and 0.032 (DYL) on
  each adapter's own Alpaca features — the DYL threshold is off by 3× across the sweep, the Apollo one by < 1 pp.
- The rank-256 arms needed vLLM `--max-lora-rank 256` for the follow-ups (fix chain; LOG 2026-09-18).

## 4. What it means for the project
Under the Apollo (mean-over-answer) pooling the cross-organism lie direction is a property of the behaviour, not of the
training run: rank, learning rate, epochs, scaling and data mix move T3 by less than the seed-to-seed noise of the
released probe. The DYL (pre-answer) readout is a less stable target: under-training and over-training both move it, and
its calibration drifts, which matches the M3 finding that DYL transfer is lower and more variable. For the paper: the
transfer claim can be stated per behaviour without a recipe caveat for the Apollo pooling; the DYL pooling needs the
"seed and recipe" caveat and per-model recalibration.

## 5. What we would do differently
Generate the follow-ups at the right LoRA rank the first time (cost: one extra GPU pass). Merge each adapter once and
extract every split in one process (the per-adapter reload dominated the feature pass). Add a second organism's sweep if
one becomes available — this is a single-organism result.
