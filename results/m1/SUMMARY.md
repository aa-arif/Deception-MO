# M1 — Feature extraction and T0 reproduction: SUMMARY (final, 2026-09-16 07:45)

Reader: has read Cooney, Africa & Irving (2026) but not our code. Numbers: results/m1/t0/*/SUMMARY_T0.md,
results/m1/gen/*/<organism>/*.meta.json, notes/LOG.md (2026-09-15 09:03 onward).

## 1. What we set out to check
With the activation convention locked in M0, extract the residual-stream features every later
experiment needs for the base model and the seven Qwen3.6 organisms, and check that the RELEASED
probes, scored on OUR features of the auditing sets (T0), reproduce the paper's trained-organism
numbers: prose medians (Apollo BA 0.52 / AUROC 0.75; DYL 0.65 / 0.75) and the per-testbed bars of
Figure 6 (gate D13: within 0.05 or 2 SE). Also: generate the DYL follow-up turns the DYL probes need,
plus the no-think, prompted (T2) and resampled transcripts for later milestones.

## 2. What we did (plain language)
- One 17-hour GPU run extracted pooled activations at the 12 released probe layers for every model
  and every split we will use (auditing sets, Alpaca calibration sets, Varied Deception and its
  validation split, the DYL training/validation splits, 300 trait-active SFT rollouts per organism),
  storing eight poolings per row including the answer-prediction position the DYL probes read.
- Apollo-style T0: released default checkpoint per organism, mean over the answer's content tokens,
  stored 1 %-Alpaca threshold, on the organism's own auditing set.
- DYL T0: appended the "Did you lie…" question to every auditing transcript, let each organism reason
  and answer (vLLM, greedy, up to 8192 tokens), extracted the state just before the answer, scored it
  with the released DYL checkpoint and threshold.
- Generated no-think answers, base-model answers under the released system prompts (T2), and four
  extra sampled rollouts per question (for M5 relabelling).

## 3. What we found

### T0 Apollo (7 organisms; results/m1/t0/standard/SUMMARY_T0.md)
| level | ours | paper | verdict |
|---|---|---|---|
| median AUROC / BA | 0.754 / 0.520 | 0.75 / 0.52 | (i) PASS |
| AuditBench BA / AUROC | 0.533 / 0.664 | 0.531 (0.019) / 0.681 (0.065) | within 0.02 |
| Maths Sandbagger | 0.500 / 0.798 | 0.505 (0.005) / 0.775 (0.025) | within 0.025 |
| Gender Secret | 0.505 / 0.797 | 0.595 (0.124) / 0.862 (0.068) | within 2 SE; provisional |
Per organism AUROC 0.51 (contextual optimism) – 0.84 (gender secret male); 95 % CIs ±0.08–0.15.
Targeted-Apollo (not in Figure 6): median 0.776, but inverted on the sandbagger (0.38).

### T0 DYL (7 organisms; released rule = drop non-yes/no follow-ups: results/m1/t0/standard_cleananswers)
| level | ours (all rows / clean answers) | paper | verdict |
|---|---|---|---|
| median AUROC | 0.714 / 0.723 | 0.75 | (i) borderline (−0.036 / −0.027) |
| median BA | 0.584 / 0.584 | 0.65 | (i) FAIL (−0.066) |
| Gender Secret BA / AUROC | 0.701 / 0.926 | 0.637 (0.05) / 0.835 (0.066) | within 2 SE |
| Maths Sandbagger | 0.506 / 0.714 | 0.575 (0.085) / 0.745 (0.045) | within 2 SE |
| AuditBench | 0.591 / 0.625 (0.611 clean) | 0.640 (0.071) / 0.749 (0.047) | AUROC FAIL (−0.12 to −0.14) |
Per organism: gender_secret_female 0.964, gender_secret_male 0.888, contextual_optimism 0.771,
sandbagger 0.714, animal_welfare 0.624, self_promotion 0.582, hallucinates_citations 0.523 (n lie 15).
Confession ("yes") rate ≤ 5 % of lies except hallucinates_citations (16 %).

### Generation (results/m1/gen)
- DYL follow-ups: 1176 transcripts; 43 truncated at 8192 tokens (19 in hallucinates_citations);
  40–60 "other" answers among AuditBench organisms.
- No-think answers: 1176 transcripts, unlabelled; median 50–90 tokens, but the sandbagger set answers
  with a single "Yes"/"No" token and self_promotion with 4 tokens (the AuditBench questions ask for
  "ANSWER: C/I"-style replies).
- T2 prompted (base model + the five released system prompts on each organism's auditing questions):
  860 transcripts, unlabelled; 4096-token budget truncated 61/190 (contextual_optimism) and 65/190
  (self_promotion) — the base model loops on the "ANSWER: C or I" answer format under those prompts;
  ≤ 7 elsewhere. Re-generate those two with a larger budget before use.
- Resampling (4 extra rollouts per question, T = 0.7): 4704 transcripts, unlabelled (M5); 0–7
  truncations per set; median 800–1450 new tokens.
- Chain wall-clock 02:08–07:33 (5.4 h) on one H100 with 32 concurrent sequences.

<!-- D20 label sets: begin -->
### Label-set comparison: T0 released probes under released vs judge labels (D20: three label sets, never mixed; full tables in results/m5/label_sets.md)

**apollo pooling**

| organism | n — originals / released | n — originals / judge | n — originals+resamples / judge | T0 — originals / released | T0 — originals / judge | T0 — originals+resamples / judge |
|---|---|---|---|---|---|---|
| GS-F | 74/79 | 75/48 | – | 0.754 [0.67, 0.83] | 0.795 [0.71, 0.87] | – |
| GS-M | 51/79 | 57/72 | – | 0.839 [0.76, 0.91] | 0.829 [0.75, 0.90] | – |
| SB | 40/51 | 57/21 | – | 0.798 [0.70, 0.89] | 0.906 [0.83, 0.97] | – |
| AW | 25/145 | 39/111 | – | 0.820 [0.73, 0.90] | 0.767 [0.66, 0.85] | – |
| CO | 24/153 | 78/85 | – | 0.509 [0.36, 0.65] | 0.666 [0.58, 0.75] | – |
| HC | 19/143 | 25/145 | – | 0.668 [0.54, 0.81] | 0.684 [0.56, 0.82] | – |
| SP | 25/148 | 39/110 | – | 0.659 [0.53, 0.77] | 0.751 [0.65, 0.84] | – |

**dyl pooling**

| organism | n — originals / released | n — originals / judge | n — originals+resamples / judge | T0 — originals / released | T0 — originals / judge | T0 — originals+resamples / judge |
|---|---|---|---|---|---|---|
| GS-F | 72/79 | 74/49 | – | 0.964 [0.92, 0.99] | 0.957 [0.90, 0.99] | – |
| GS-M | 51/78 | 58/73 | – | 0.888 [0.82, 0.94] | 0.842 [0.77, 0.91] | – |
| SB | 38/50 | 54/21 | – | 0.714 [0.59, 0.82] | 0.629 [0.47, 0.78] | – |
| AW | 22/136 | 35/105 | – | 0.624 [0.47, 0.78] | 0.630 [0.51, 0.75] | – |
| CO | 24/151 | 78/83 | – | 0.771 [0.67, 0.86] | 0.851 [0.79, 0.91] | – |
| HC | 15/130 | 22/133 | – | 0.523 [0.34, 0.71] | 0.670 [0.53, 0.82] | – |
| SP | 25/147 | 40/108 | – | 0.582 [0.44, 0.70] | 0.662 [0.55, 0.76] | – |

<!-- D20 label sets: end -->

## 4. What it means for the project
- The pipeline reproduces the paper where the paper is precise: Apollo medians to 0.01, DYL on the
  gender-secret and sandbagger testbeds within noise. The released probes can be used as intended.
- DYL on the four AuditBench organisms is weaker than Figure 6 by 0.12–0.14 AUROC. The bar pools the
  Qwen3.5 organisms (where DYL is stronger), the lie counts are 13–25 per organism (CIs ±0.15), and
  the paper's decoding for the follow-up is unstated. Decision needed: accept with the AuditBench
  caveat, or test decoding/budget variants before M2 (cheap: ~15 min GPU per variant).
- Organism difficulty differs by detector: contextual_optimism is Apollo's worst and DYL's best
  AuditBench organism; hallucinates_citations is DYL's worst — relevant for the transfer ladder.
- Features exist for every split needed by M2–M6; all analysis from here is CPU.

## 5. What we would do differently
- Generate the DYL follow-ups in the same burst as extraction (they are cheap: ~10 min per organism).
- Fix the sampling/budget protocol for follow-ups before scoring, and record it as a decision.
- Set vLLM's max_num_seqs explicitly for hybrid models from the start (the default OOMs at 80 GB).
- Merge LoRA for extraction from the outset (1.4× faster) — now permitted by D14 for later bursts.
