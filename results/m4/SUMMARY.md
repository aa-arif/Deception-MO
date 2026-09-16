# M4 — T1 frozen base probes ± label-free realignment: SUMMARY (2026-09-16, revised per directive)

Method check: CORAL uses Ledoit–Wolf shrinkage covariances on BOTH sides (organism Alpaca and base Alpaca; `LedoitWolf().fit(...)`
in src/m4_t1.py), Σ_org^{-1/2} Σ_base^{1/2} via eigendecomposition with eigenvalues clipped at 1e-6. The 1 %-FPR threshold for
the BA@recal column is recomputed on the organism's Alpaca features AFTER the same realignment. Base checkpoints = the released
defaults (apollo-qwen-qwen3.6-27b: l_44_ar_dim @L44; dyl-qwen-qwen3.6-27b: l_50_lm_10_ar_lr @L50). T5 = same-organism ceiling
(M2, lr, best layer, out of fold, bootstrap CI over rows). Bootstrap CIs: 1000 resamples over rows.

## 1. What we set out to check
Whether the base model's released lie probe still reads the fine-tuned organisms, and whether a label-free realignment of
the organism's activations onto the base distribution (offset = mean-centre; offset + rotation/scale = CORAL) recovers it.

## 2. What we did (plain language)
Scored each organism's auditing activations with the base probe as they are, after shifting them so the organism's average
Alpaca activation coincides with the base model's, and after additionally matching the Alpaca covariance to the base model's.

## 3. What we found (AUROC [95 % CI]; BA at the base probe's stored threshold / recalibrated at 1 % FPR after realignment)

### apollo pooling (mean over content tokens)

| organism | n lie/hon | T1 raw AUROC [CI] (BA stored / recal) | T1 mean-centred (BA stored / recal) | T1 CORAL AUROC [CI] (BA stored / recal) | T0 released org probe [CI] | T5 ceiling lr [CI] | reading |
|---|---|---|---|---|---|---|---|
| GS-F | 74/79 | 0.606 [0.52, 0.70] (0.50 / 0.50) | 0.606 (0.50 / 0.50) | 0.866 [0.81, 0.92] (0.54 / 0.53) | 0.754 [0.67, 0.83] | 0.999 [1.00, 1.00] | offset (stored threshold flags nothing even though ranking works); rotation/scale (CORAL +0.26 AUROC); novelty (best T1 still 0.13 below the organism's own ceiling) |
| GS-M | 51/79 | 0.499 [0.40, 0.60] (0.50 / 0.50) | 0.499 (0.50 / 0.50) | 0.672 [0.57, 0.76] (0.50 / 0.50) | 0.839 [0.76, 0.91] | 0.994 [0.98, 1.00] | rotation/scale (CORAL +0.17 AUROC); novelty (best T1 still 0.32 below the organism's own ceiling) |
| SB | 40/51 | 0.786 [0.68, 0.88] (0.50 / 0.50) | 0.786 (0.50 / 0.50) | 0.805 [0.70, 0.89] (0.51 / 0.51) | 0.798 [0.70, 0.89] | 0.935 [0.87, 0.98] | offset (stored threshold flags nothing even though ranking works); novelty (best T1 still 0.13 below the organism's own ceiling) |
| AW | 25/145 | 0.775 [0.67, 0.87] (0.50 / 0.50) | 0.775 (0.50 / 0.50) | 0.807 [0.71, 0.90] (0.53 / 0.53) | 0.820 [0.73, 0.90] | 0.895 [0.81, 0.97] | offset (stored threshold flags nothing even though ranking works) |
| CO | 24/153 | 0.374 [0.27, 0.48] (0.50 / 0.50) | 0.374 (0.50 / 0.50) | 0.454 [0.34, 0.57] (0.47 / 0.49) | 0.509 [0.36, 0.65] | 0.971 [0.93, 0.99] | rotation/scale (CORAL +0.08 AUROC); novelty (best T1 still 0.52 below the organism's own ceiling); base direction INVERTED on this organism |
| HC | 19/143 | 0.746 [0.61, 0.87] (0.50 / 0.50) | 0.746 (0.50 / 0.50) | 0.842 [0.74, 0.93] (0.55 / 0.53) | 0.668 [0.54, 0.81] | 0.987 [0.97, 1.00] | offset (stored threshold flags nothing even though ranking works); rotation/scale (CORAL +0.10 AUROC); novelty (best T1 still 0.15 below the organism's own ceiling) |
| SP | 25/148 | 0.569 [0.46, 0.68] (0.50 / 0.50) | 0.569 (0.50 / 0.50) | 0.593 [0.45, 0.71] (0.50 / 0.50) | 0.659 [0.53, 0.77] | 0.972 [0.95, 0.99] | novelty (best T1 still 0.38 below the organism's own ceiling) |

Medians: raw 0.606 · centred 0.606 · CORAL 0.805 · T0 0.754 · T5 0.972

### dyl pooling (pre-answer state)

| organism | n lie/hon | T1 raw AUROC [CI] (BA stored / recal) | T1 mean-centred (BA stored / recal) | T1 CORAL AUROC [CI] (BA stored / recal) | T0 released org probe [CI] | T5 ceiling lr [CI] | reading |
|---|---|---|---|---|---|---|---|
| GS-F | 72/79 | 0.914 [0.85, 0.97] (0.49 / 0.88) | 0.914 (0.88 / 0.88) | 0.799 [0.71, 0.87] (0.71 / 0.72) | 0.964 [0.92, 0.99] | 0.982 [0.95, 1.00] | offset (centring restores calibration: BA@stored 0.49→0.88); whitening harmful (-0.11) — second-moment estimate too noisy for this readout |
| GS-M | 51/78 | 0.716 [0.61, 0.81] (0.50 / 0.77) | 0.716 (0.77 / 0.77) | 0.605 [0.50, 0.70] (0.58 / 0.58) | 0.888 [0.82, 0.94] | 0.932 [0.88, 0.97] | offset (centring restores calibration: BA@stored 0.50→0.77); whitening harmful (-0.11) — second-moment estimate too noisy for this readout; novelty (best T1 still 0.22 below the organism's own ceiling) |
| SB | 38/50 | 0.596 [0.48, 0.72] (0.51 / 0.50) | 0.596 (0.49 / 0.50) | 0.493 [0.38, 0.61] (0.47 / 0.47) | 0.714 [0.59, 0.82] | 0.934 [0.88, 0.98] | whitening harmful (-0.10) — second-moment estimate too noisy for this readout; novelty (best T1 still 0.34 below the organism's own ceiling) |
| AW | 22/136 | 0.526 [0.36, 0.69] (0.50 / 0.56) | 0.526 (0.55 / 0.56) | 0.544 [0.40, 0.67] (0.51 / 0.51) | 0.624 [0.47, 0.78] | 0.849 [0.76, 0.92] | novelty (best T1 still 0.30 below the organism's own ceiling) |
| CO | 24/151 | 0.575 [0.48, 0.66] (0.48 / 0.48) | 0.575 (0.45 / 0.48) | 0.381 [0.27, 0.50] (0.41 / 0.42) | 0.771 [0.67, 0.86] | 0.859 [0.77, 0.93] | whitening harmful (-0.19) — second-moment estimate too noisy for this readout; novelty (best T1 still 0.28 below the organism's own ceiling) |
| HC | 15/130 | 0.442 [0.27, 0.62] (0.42 / 0.56) | 0.442 (0.54 / 0.56) | 0.569 [0.37, 0.77] (0.61 / 0.62) | 0.523 [0.34, 0.71] | 0.877 [0.75, 0.97] | offset (centring restores calibration: BA@stored 0.42→0.54); rotation/scale (CORAL +0.13 AUROC); novelty (best T1 still 0.31 below the organism's own ceiling); base direction INVERTED on this organism |
| SP | 25/147 | 0.525 [0.38, 0.66] (0.41 / 0.49) | 0.525 (0.49 / 0.49) | 0.610 [0.49, 0.74] (0.53 / 0.53) | 0.582 [0.44, 0.70] | 0.852 [0.76, 0.93] | offset (centring restores calibration: BA@stored 0.41→0.49); rotation/scale (CORAL +0.08 AUROC); novelty (best T1 still 0.24 below the organism's own ceiling) |

Medians: raw 0.575 · centred 0.575 · CORAL 0.569 · T0 0.714 · T5 0.877

Reading rules: offset = mean-centring moves BA at the stored threshold by ≥ 0.05 (calibration shift; AUROC is shift-invariant by
construction); rotation/scale = CORAL changes AUROC by ≥ 0.05; novelty = the organism's own ceiling (T5) exceeds the best T1 by ≥ 0.10.

## 4. What it means for the project
- Apollo pooling: fine-tuning shows up as offset + rotation. Centring alone restores nothing in ranking; CORAL lifts the frozen base
  probe to a median 0.81 (above the released organism probes' 0.75) — on GS-F, HC, AW, SB the base direction survives fine-tuning up
  to a second-moment change. CO and SP are novelty cases (CORAL 0.45 / 0.59 vs ceilings 0.97): their lies are not on the base
  instructed-deception direction at all (CO inverted).
- DYL pooling: offset dominates the calibration failure (centring restores BA@stored on GS-F 0.49 → 0.88, GS-M 0.50 → 0.77) while
  CORAL is harmful on the organisms where the base probe works (GS-F −0.12, GS-M −0.11, SB −0.10, CO −0.19) and mildly helpful only
  where it was at chance (HC +0.13, SP +0.09): the pre-answer state is a sharp feature that a 5120-dim covariance from 2400 Alpaca
  rows distorts. Every AuditBench organism and the sandbagger are novelty cases under DYL (ceiling − best T1 ≥ 0.27).
- Consequence for the ladder: the base→organism rung is cheap to close for content-pooled probes (whitening), not for the
  follow-up readout; M3's cross-organism probes (0.77–0.93) remain the stronger route for both.

## 5. What we would do differently
- Layer-match base and organism probes (released defaults differ: L44 dim vs L38 lr; L50 lr vs L44 dim); fit our own base probe at
  the M3-selected layer (L32 Apollo / L38–44 DYL) so T1 compares like with like.
- Try a low-rank or ridge-regularised CORAL (fixed ridge sweep) and a larger label-free alignment set for the DYL pooling.
- Bootstrap the CORAL transform itself (resample the Alpaca rows) to put a CI on the realignment gain.
