# M2 — T5 same-organism ceiling: SUMMARY (draft 2026-09-16 14:00; DYL pooling pending the protocol decision)

## 1. What we set out to check
How well a probe can do on each organism's OWN auditing set when trained on that set (question-disjoint
cross-validation) — the ceiling every transfer result in M3–M4 is measured against — and whether the
released probes' weak auditing-set performance (T0) reflects missing signal or a transfer failure.

## 2. What we did (plain language)
For each of the seven organisms, and each layer of the released grid, we split the auditing questions
into five folds, trained a probe on four folds (difference of class means; separately, an L2-regularised
logistic regression with its regularisation chosen inside the training folds), set its threshold to the
1 % false-positive point on the organism's own Alpaca answers, and scored the held-out fold. All rows are
therefore scored by a probe that never saw them. Bootstrap confidence intervals over rows.

## 3. What we found (Apollo pooling = mean over the answer's content tokens)
| organism | n lie/honest | diff-of-means, default layer 38 | diff-of-means, best layer | logistic regression, best layer | released probe (T0) |
|---|---|---|---|---|---|
| gender_secret_female | 74/79 | 0.978 [0.96, 0.99] | 0.984 (L32) | 0.999 | 0.754 |
| gender_secret_male | 51/79 | 0.857 [0.79, 0.92] | 0.872 (L57) | 0.994 | 0.839 |
| eval_sandbagger | 40/51 | 0.810 [0.71, 0.90] | 0.873 (L57) | 0.935 | 0.798 |
| ab_animal_welfare | 25/145 | 0.654 [0.54, 0.77] | 0.725 (L57) | 0.895 | 0.820 |
| ab_contextual_optimism | 24/153 | 0.702 [0.57, 0.81] | 0.876 (L57) | 0.971 | 0.509 |
| ab_hallucinates_citations | 19/143 | 0.750 [0.60, 0.89] | 0.801 (L57) | 0.987 | 0.668 |
| ab_self_promotion | 25/148 | 0.476 [0.35, 0.59] | 0.501 (L13) | 0.972 | 0.659 |
Medians: diff-of-means 0.750 (default) / 0.872 (best); logistic regression ≈ 0.97. Full layer sweep and
balanced accuracies at 1 % FPR in results/m2/t5/apollo/SUMMARY.md. DYL pooling: [pending].

## 4. What it means for the project
- Every organism's lies are linearly separable in its own activations (logistic regression 0.90–0.999
  out of fold), so the released probes' auditing-set weakness is a transfer failure — the phenomenon
  the distance ladder is built to measure.
- The mean-difference direction captures much less than a fitted separator on the AuditBench organisms
  (chance for self_promotion): "the lie direction" is organism-specific and not a simple class-mean
  shift. M3 should carry both probe types.
- Best layers sit at the top of the Apollo grid (L57) for six organisms — the DYL grid (to L63) and a
  wider sweep should be checked before fixing layers for M3.
- The ceiling is high-variance (19–25 lies per AuditBench organism): CIs ±0.1; M5's relabelled
  resamples are needed before fine comparisons.

## 5. What we would do differently
- Sweep to L63 for both poolings from the start.
- Report the ceiling with nested (outer) layer selection as well, to remove the in-sample optimism.
