# M3 — cross-organism transfer: SUMMARY (2026-09-16)

## 1. What we set out to check
How far a lie probe trained on OTHER organisms transfers to a held-out organism (T3: leave one organism out) and
to a held-out FAMILY of organisms (T4: gender-secret pair / AuditBench four / sandbagger), against the released
per-organism probes (T0) and the same-organism ceiling (T5). All hyperparameters (layer, estimator, λ) were
chosen by an inner leave-one-organism-out over the training organisms only (CLAUDE.md rule 6). Because the
four AuditBench organisms share one 190-question list (and the two gender organisms one 158-question list),
every transfer was run twice: with the training organisms' rows on the held-out organism's target questions
kept ('leak' — they are honest controls for the other organisms) and removed ('noleak').

## 2. What we did (plain language)
For every held-out organism we pooled the auditing-set activations of the training organisms (graded labels,
ambiguous dropped), fitted an L2 logistic regression (primary, D16), a difference-of-means and a shrinkage
(whitened) difference-of-means, picked the layer and regularisation that best predicted lies on each of the
training organisms in turn, then scored the held-out organism once. AUROC with bootstrap CIs over rows;
balanced accuracy at the 1 %-FPR threshold set on the held-out organism's own Alpaca answers (label-free).

## 3. What we found — lr AUROC per organism, side by side (T5 = same-organism ceiling, best layer, out of fold)

### apollo pooling (mean over content tokens)

| organism | T0 released | T1 base+CORAL | T3 leak | T3 noleak [CI] | T4 (family out) [CI] | T5 ceiling | T5 − T3 noleak | T3 noleak − T0 |
|---|---|---|---|---|---|---|---|---|
| GS-F | 0.754 | 0.866 | 0.997 | 0.976 [0.95, 1.00] | 0.981 [0.95, 1.00] | 0.999 | +0.024 | +0.222 |
| GS-M | 0.839 | 0.672 | 0.990 | 0.957 [0.92, 0.99] | 0.941 [0.89, 0.98] | 0.994 | +0.037 | +0.118 |
| SB | 0.798 | 0.805 | 0.821 | 0.821 [0.73, 0.90] | 0.821 [0.73, 0.90] | 0.935 | +0.114 | +0.023 |
| AW | 0.820 | 0.807 | 0.902 | 0.934 [0.89, 0.97] | 0.574 [0.46, 0.68] | 0.895 | -0.039 | +0.113 |
| CO | 0.509 | 0.454 | 0.877 | 0.931 [0.89, 0.97] | 0.909 [0.86, 0.95] | 0.971 | +0.040 | +0.423 |
| HC | 0.668 | 0.842 | 0.913 | 0.923 [0.85, 0.98] | 0.690 [0.56, 0.81] | 0.987 | +0.064 | +0.254 |
| SP | 0.659 | 0.593 | 0.869 | 0.909 [0.83, 0.96] | 0.662 [0.53, 0.78] | 0.972 | +0.064 | +0.250 |

Medians: T0 0.754 · T1+CORAL 0.805 · T3 leak 0.902 · T3 noleak 0.931 · T4 0.821 · T5 0.972; median T5 − T3(noleak) +0.040.

### dyl pooling (pre-answer state of the generated follow-up)

| organism | T0 released | T1 base+CORAL | T3 leak | T3 noleak [CI] | T4 (family out) [CI] | T5 ceiling | T5 − T3 noleak | T3 noleak − T0 |
|---|---|---|---|---|---|---|---|---|
| GS-F | 0.964 | 0.799 | 0.990 | 0.975 [0.94, 1.00] | 0.975 [0.94, 1.00] | 0.982 | +0.007 | +0.011 |
| GS-M | 0.888 | 0.605 | 0.949 | 0.909 [0.86, 0.95] | 0.901 [0.85, 0.95] | 0.932 | +0.023 | +0.021 |
| SB | 0.714 | 0.493 | 0.787 | 0.787 [0.67, 0.88] | 0.787 [0.67, 0.88] | 0.934 | +0.147 | +0.073 |
| AW | 0.624 | 0.544 | 0.791 | 0.746 [0.63, 0.86] | 0.498 [0.36, 0.63] | 0.849 | +0.102 | +0.123 |
| CO | 0.771 | 0.381 | 0.743 | 0.768 [0.67, 0.86] | 0.715 [0.61, 0.81] | 0.859 | +0.091 | -0.003 |
| HC | 0.523 | 0.569 | 0.658 | 0.729 [0.58, 0.87] | 0.779 [0.61, 0.93] | 0.877 | +0.148 | +0.206 |
| SP | 0.582 | 0.610 | 0.727 | 0.741 [0.62, 0.85] | 0.614 [0.52, 0.71] | 0.852 | +0.111 | +0.159 |

Medians: T0 0.714 · T1+CORAL 0.569 · T3 leak 0.787 · T3 noleak 0.768 · T4 0.779 · T5 0.877; median T5 − T3(noleak) +0.102.

Secondary estimators, BA at 1 % FPR and the selected hyperparameters are in results/m3/{apollo,dyl}/SUMMARY.md.

## 4. What it means for the project
- Under the Apollo pooling, a probe trained on the OTHER organisms transfers almost to the ceiling: median T3 noleak
  0.93 vs T5 0.97 (gap 0.02–0.11), and beats the released per-organism probes on every organism (median +0.18;
  contextual_optimism 0.51 → 0.93). The released probes' failure is not a failure of linear probes — it is a
  failure of the instructed-pairs training distribution. Trained-organism lies are a shared, linearly readable
  signal across behaviours.
- Holding out the whole FAMILY (T4) is where Apollo-pooling transfer breaks for three AuditBench organisms
  (AW 0.57, HC 0.69, SP 0.66) while GS-F/GS-M/CO/SB stay at 0.82–0.98: the AuditBench 'withhold / slant'
  behaviours share structure with each other more than with gender secrecy or sandbagging. That is the
  first rung-gap of the distance ladder (same family → other family).
- Under the DYL pooling the same ordering holds at lower levels (T3 noleak 0.77, T5 0.88, T0 0.71): the
  pre-answer state carries a shared signal too, but less of it.
- 'noleak' ≥ 'leak' for the AuditBench organisms: removing the training organisms' honest answers to the
  held-out organism's own questions HELPS — those rows teach the probe that the held-out topic is honest.
- The shrinkage diff-of-means tracks lr closely (within 0.02–0.08); the raw diff-of-means does not (0.48–0.77):
  the transferable direction lives in the whitened metric (D16 confirmed).
- Inner selection chose L32 with weak regularisation (C = 1) for every Apollo-pooling case and L38/L44 with
  C = 0.01 for DYL: the transfer layer sits below the released defaults.

## 5. What we would do differently
- Sweep layers 25–44 at finer granularity for transfer; the released grids were built for same-model probes.
- Report T3 with a nested outer bootstrap over training-organism subsets to quantify how much each donor matters.
- Add the T1+CORAL baseline to every transfer table by default — it is the cheapest competitor (median 0.81).
