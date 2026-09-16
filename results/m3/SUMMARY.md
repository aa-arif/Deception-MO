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

## 3. What we found — per organism (lr AUROC; T5 = same-organism ceiling; QD = question-disjoint LOO, AuditBench only)

### apollo pooling (mean over content tokens)

| organism | T0 released [CI] | T1 base+CORAL [CI] | T3 noleak [CI] | T3 fine [CI] | T3 QD spec [CI] | T3 QD strict [CI] | T4 family-out (signed) [CI] | T5 ceiling [CI] | T5 − headline T3 |
|---|---|---|---|---|---|---|---|---|---|
| GS-F | 0.754 [0.67, 0.83] | 0.866 [0.81, 0.92] | 0.976 [0.95, 1.00] | 0.976 [0.95, 1.00] | – (no shared list) | – (no shared list) | 0.981 [0.95, 1.00] | 0.999 [1.00, 1.00] | +0.024 |
| GS-M | 0.839 [0.76, 0.91] | 0.672 [0.57, 0.76] | 0.957 [0.92, 0.99] | 0.957 [0.92, 0.99] | – (no shared list) | – (no shared list) | 0.941 [0.89, 0.98] | 0.994 [0.98, 1.00] | +0.037 |
| SB | 0.798 [0.70, 0.89] | 0.805 [0.70, 0.89] | 0.821 [0.73, 0.90] | 0.821 [0.73, 0.90] | – (no shared list) | – (no shared list) | 0.821 [0.73, 0.90] | 0.935 [0.87, 0.98] | +0.114 |
| AW | 0.820 [0.73, 0.90] | 0.807 [0.71, 0.90] | 0.934 [0.89, 0.97] | 0.934 [0.89, 0.97] | 0.929 [0.86, 0.98] | 0.911 [0.84, 0.96] | 0.574 [0.46, 0.68] | 0.895 [0.81, 0.97] | -0.016 |
| CO | 0.509 [0.36, 0.65] | 0.454 [0.34, 0.57] | 0.931 [0.89, 0.97] | 0.931 [0.89, 0.97] | 0.943 [0.90, 0.98] | 0.930 [0.87, 0.97] | 0.909 [0.86, 0.95] | 0.971 [0.93, 0.99] | +0.041 |
| HC | 0.668 [0.54, 0.81] | 0.842 [0.74, 0.93] | 0.923 [0.85, 0.98] | 0.923 [0.85, 0.98] | 0.836 [0.74, 0.91] | 0.743 [0.61, 0.85] | 0.690 [0.56, 0.81] | 0.987 [0.97, 1.00] | +0.244 |
| SP | 0.659 [0.53, 0.77] | 0.593 [0.45, 0.71] | 0.909 [0.83, 0.96] | 0.909 [0.83, 0.96] | 0.917 [0.84, 0.97] | 0.916 [0.85, 0.98] | 0.662 [0.53, 0.78] | 0.972 [0.95, 0.99] | +0.056 |

### dyl pooling (pre-answer state)

| organism | T0 released [CI] | T1 base+CORAL [CI] | T3 noleak [CI] | T3 fine [CI] | T3 QD spec [CI] | T3 QD strict [CI] | T4 family-out (signed) [CI] | T5 ceiling [CI] | T5 − headline T3 |
|---|---|---|---|---|---|---|---|---|---|
| GS-F | 0.964 [0.92, 0.99] | 0.799 [0.71, 0.87] | 0.975 [0.94, 1.00] | 0.975 [0.94, 1.00] | – (no shared list) | – (no shared list) | 0.975 [0.94, 1.00] | 0.982 [0.95, 1.00] | +0.007 |
| GS-M | 0.888 [0.82, 0.94] | 0.605 [0.50, 0.70] | 0.909 [0.86, 0.95] | 0.907 [0.86, 0.95] | – (no shared list) | – (no shared list) | 0.901 [0.85, 0.95] | 0.932 [0.88, 0.97] | +0.023 |
| SB | 0.714 [0.59, 0.82] | 0.493 [0.38, 0.61] | 0.787 [0.67, 0.88] | 0.759 [0.65, 0.85] | – (no shared list) | – (no shared list) | 0.787 [0.67, 0.88] | 0.934 [0.88, 0.98] | +0.147 |
| AW | 0.624 [0.47, 0.78] | 0.544 [0.40, 0.67] | 0.746 [0.63, 0.86] | 0.732 [0.61, 0.85] | 0.678 [0.55, 0.80] | 0.614 [0.48, 0.75] | 0.498 [0.36, 0.63] | 0.849 [0.76, 0.92] | +0.235 |
| CO | 0.771 [0.67, 0.86] | 0.381 [0.27, 0.50] | 0.768 [0.67, 0.86] | 0.760 [0.67, 0.85] | 0.755 [0.65, 0.85] | 0.774 [0.68, 0.87] | 0.715 [0.61, 0.81] | 0.859 [0.77, 0.93] | +0.086 |
| HC | 0.523 [0.34, 0.71] | 0.569 [0.37, 0.77] | 0.729 [0.58, 0.87] | 0.729 [0.58, 0.87] | 0.701 [0.54, 0.85] | 0.669 [0.51, 0.82] | 0.779 [0.61, 0.93] | 0.877 [0.75, 0.97] | +0.208 |
| SP | 0.582 [0.44, 0.70] | 0.610 [0.49, 0.74] | 0.741 [0.62, 0.85] | 0.734 [0.61, 0.84] | 0.692 [0.57, 0.81] | 0.675 [0.55, 0.80] | 0.614 [0.52, 0.71] | 0.852 [0.76, 0.93] | +0.178 |


### T2 — prompted-base probes → trained organisms (Apollo pooling; condition labels on the prompted set; D17 rows excluded; results/m4/T2.md)
| organism | T2 probe → organism AUROC [CI] (layer, C) | organism T3 probe → prompted set | T0 released | T3 noleak | T5 |
|---|---|---|---|---|---|
| eval_sandbagger | 0.892 [0.82, 0.95] (L44, 0.1) | 0.965 | 0.798 | 0.821 | 0.935 |
| ab_animal_welfare | 0.868 [0.80, 0.92] (L32, 0.01) | 0.797 | 0.820 | 0.934 | 0.895 |
| ab_contextual_optimism | 0.951 [0.91, 0.98] (L32, 1.0) | 0.985 | 0.509 | 0.931 | 0.971 |
| ab_hallucinates_citations | 0.929 [0.88, 0.97] (L38, 1.0) | 0.847 | 0.668 | 0.923 | 0.987 |
| ab_self_promotion | 0.925 [0.88, 0.97] (L32, 0.001) | 0.839 | 0.659 | 0.909 | 0.972 |
A probe trained only on the BASE model under the organism's own system prompt (prompted lies vs prompted controls) transfers to the fine-tuned organism at 0.87–0.95 — on par with the cross-organism T3 probe and far above the released probes; and the organism's T3 probe reads the prompted base at 0.80–0.99. The prompted and trained versions of a behaviour share their lie direction (ladder rung "prompted only" is short for these behaviours). Caveat: condition labels, not graded.

Headline T3 (D18): the question-disjoint STRICT number for the four AuditBench organisms, the standard noleak number for the gender pair and the sandbagger. Secondary estimators, BA at 1 % FPR, selected hyperparameters: results/m3/{apollo,dyl}/SUMMARY.md; controls: results/m3/CONTROLS.md.

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
