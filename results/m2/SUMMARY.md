# M2 — T5 same-organism ceiling: SUMMARY (final, 2026-09-16 14:30)

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
balanced accuracies at 1 % FPR in results/m2/t5/apollo/SUMMARY.md.

### DYL pooling (state before the yes/no answer of the generated follow-up; greedy protocol, D15)
| organism | n lie/honest | diff-of-means, default layer 44 | diff-of-means, best layer | logistic regression, best layer | released probe (T0) |
|---|---|---|---|---|---|
| gender_secret_female | 72/79 | 0.925 [0.88, 0.96] | 0.937 (L38) | 0.982 | 0.964 |
| gender_secret_male | 51/78 | 0.863 [0.79, 0.93] | 0.873 (L38) | 0.932 | 0.888 |
| eval_sandbagger | 38/50 | 0.704 [0.59, 0.81] | 0.759 (L38) | 0.934 | 0.714 |
| ab_animal_welfare | 22/136 | 0.422 [0.29, 0.54] | 0.531 (L38) | 0.849 | 0.624 |
| ab_contextual_optimism | 24/151 | 0.638 [0.50, 0.76] | 0.684 (L62) | 0.859 | 0.771 |
| ab_hallucinates_citations | 15/130 | 0.503 [0.35, 0.65] | 0.569 (L38) | 0.877 | 0.523 |
| ab_self_promotion | 25/147 | 0.543 [0.42, 0.67] | 0.574 (L38) | 0.852 | 0.582 |
Medians: diff-of-means 0.638 (default) / 0.684 (best); logistic regression ≈ 0.86. The released DYL probes
match or beat the same-set diff-of-means for five organisms — a direction learned from 5000 city-country
lies generalises better than one fitted to 150 auditing rows.

<!-- D20 label sets: begin -->
### Label-set comparison: T5 ceiling under released vs judge labels (D20: three label sets, never mixed; full tables in results/m5/label_sets.md)

**apollo pooling**

| organism | n — originals / released | n — originals / judge | n — originals+resamples / judge | T5 — originals / released | T5 — originals / judge | T5 — originals+resamples / judge |
|---|---|---|---|---|---|---|
| GS-F | 74/79 | 75/48 | 383/246 | 0.999 [1.00, 1.00] (L32) | 1.000 [1.00, 1.00] (L32) | 1.000 [1.00, 1.00] (L38) |
| GS-M | 51/79 | 57/72 | 293/355 | 0.994 [0.98, 1.00] (L57) | 0.963 [0.93, 0.99] (L38) | 0.968 [0.95, 0.98] (L57) |
| SB | 40/51 | 57/21 | 286/142 | 0.935 [0.87, 0.98] (L57) | 0.958 [0.92, 0.99] (L57) | 0.967 [0.94, 0.98] (L57) |
| AW | 25/145 | 39/111 | 210/557 | 0.895 [0.81, 0.97] (L57) | 0.846 [0.77, 0.92] (L57) | 0.917 [0.88, 0.94] (L57) |
| CO | 24/153 | 78/85 | 398/403 | 0.971 [0.93, 0.99] (L57) | 0.835 [0.77, 0.89] (L57) | 0.889 [0.86, 0.92] (L57) |
| HC | 19/143 | 25/145 | 165/697 | 0.987 [0.97, 1.00] (L57) | 0.861 [0.78, 0.93] (L57) | 0.936 [0.91, 0.96] (L57) |
| SP | 25/148 | 39/110 | 199/573 | 0.972 [0.95, 0.99] (L13) | 0.899 [0.83, 0.96] (L32) | 0.909 [0.87, 0.94] (L13) |

**dyl pooling**

| organism | n — originals / released | n — originals / judge | n — originals+resamples / judge | T5 — originals / released | T5 — originals / judge | T5 — originals+resamples / judge |
|---|---|---|---|---|---|---|
| GS-F | 72/79 | 74/49 | – | 0.982 [0.95, 1.00] (L38) | 0.984 [0.95, 1.00] (L38) | – |
| GS-M | 51/78 | 58/73 | – | 0.932 [0.88, 0.97] (L38) | 0.815 [0.74, 0.88] (L38) | – |
| SB | 38/50 | 54/21 | – | 0.934 [0.88, 0.98] (L38) | 0.845 [0.73, 0.93] (L57) | – |
| AW | 22/136 | 35/105 | – | 0.849 [0.76, 0.92] (L38) | 0.738 [0.63, 0.83] (L38) | – |
| CO | 24/151 | 78/83 | – | 0.859 [0.77, 0.93] (L62) | 0.813 [0.74, 0.88] (L54) | – |
| HC | 15/130 | 22/133 | – | 0.877 [0.75, 0.97] (L38) | 0.777 [0.65, 0.89] (L54) | – |
| SP | 25/147 | 40/108 | – | 0.852 [0.76, 0.93] (L38) | 0.787 [0.68, 0.88] (L38) | – |

<!-- D20 label sets: end -->

## 4. What it means for the project
- Every organism's lies are linearly separable in its own activations (logistic regression 0.90–0.999
  out of fold), so the released probes' auditing-set weakness is a transfer failure — the phenomenon
  the distance ladder is built to measure.
- The mean-difference direction captures much less than a fitted separator on the AuditBench organisms
  (chance for self_promotion): "the lie direction" is organism-specific and not a simple class-mean
  shift. M3 should carry both probe types.
- Best layers sit at the top of the Apollo grid (L57) for six organisms under content-mean pooling and at
  the bottom of the DYL grid (L38) under pre-answer pooling: the L38–L57 band is where M3 should sweep.
- The pre-answer readout is less separable than the content mean (lr 0.86 vs 0.97): the DYL follow-up
  compresses the evidence into one state; the lie's own tokens carry more.
- The ceiling is high-variance (19–25 lies per AuditBench organism): CIs ±0.1; M5's relabelled
  resamples are needed before fine comparisons.

## 5. What we would do differently
- Sweep to L63 for both poolings from the start.
- Report the ceiling with nested (outer) layer selection as well, to remove the in-sample optimism.
