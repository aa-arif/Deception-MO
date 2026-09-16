# M4 — T1 frozen base probes ± realignment (T2 prompted pending labels): SUMMARY (2026-09-16)

## 1. What we set out to check
Whether a lie probe trained on the UNMODIFIED base model (the released apollo-/dyl-qwen-qwen3.6-27b
checkpoints) still works on the fine-tuned organisms, and whether a label-free realignment of the
organism's activations onto the base model's distribution — mean-centring, then CORAL whitening, both
fitted on Alpaca completions only — recovers what fine-tuning broke.

## 2. What we did (plain language)
For each organism we scored its auditing-set activations with the base model's released probe three
ways: as they are; shifted so that the organism's average Alpaca activation coincides with the base
model's; and additionally rotated/scaled so that the organism's Alpaca covariance matches the base
model's. AUROC with bootstrap CIs; balanced accuracy at the base probe's stored threshold and at a
threshold recalibrated at 1 % FPR on the transformed Alpaca features.

## 3. What we found (median AUROC over 7 organisms; per organism in results/m4/t1/SUMMARY.md)
| family | raw | mean-centred | CORAL | released organism-specific probes (T0) |
|---|---|---|---|---|
| Apollo (mean over content tokens) | 0.606 | 0.606 | 0.805 | 0.754 |
| DYL (pre-answer state) | 0.575 | 0.575 | 0.569 | 0.714 |
- Mean-centring never changes AUROC (a linear probe's ranking is shift-invariant) but restores the
  stored threshold: base DYL on gender_secret_female goes from BA 0.49 to 0.88 at the stored threshold.
- CORAL lifts the frozen base Apollo probe above the organism-specific released probes on 4/7
  organisms (GS-F 0.87, HC 0.84, SB 0.81, AW 0.81) and to a median of 0.81; it does not rescue the two
  hardest (CO 0.45, SP 0.59).
- For DYL, CORAL hurts wherever the base probe already worked (GS-F 0.91 → 0.80) and helps only the
  AuditBench organisms near chance; the pre-answer state is a sharp single-token feature that a
  5120-dim covariance estimated from 2400 Alpaca rows distorts.
- The base Apollo probe is inverted on contextual_optimism (0.37).

## 4. What it means for the project
- For Apollo-style probes, fine-tuning mostly moves the SECOND moment of the feature distribution:
  a label-free whitening recovers a base-model probe to organism-probe level. This is a strong,
  cheap baseline that every rung of the ladder must beat, and it argues that the "lie direction"
  itself transfers from base to organism better than raw scores suggest.
- For DYL-style probes the failure is not a distribution shift that Alpaca-fitted moments capture;
  the transfer question there is about the direction (M3, M6).
- Calibration must be redone per subject model even when the probe is frozen (centring alone fixes it).

## 5. What we would do differently
- Layer-match base and organism probes (the released defaults differ: base Apollo L44 dim vs organism
  L38 lr; base DYL L50 lr vs organism L44 dim); use our own base probes at the M3-selected layer.
- Fit CORAL with a low-rank or shrunk covariance and test it on the DYL feature; try whitening on a
  larger label-free set (Varied Deception honest rows) for the single-token pooling.
