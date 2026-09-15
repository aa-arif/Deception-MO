# M0 — Environment and convention lock: SUMMARY (final, 2026-09-15 08:35)

Reader: has read Cooney, Africa & Irving (2026) but not our code. Numbers: results/m0/lock/*.md,
results/m0/dyl_tail/*.md, results/m0/lock_followup.json, results/m0/sanity.json.

## 1. What we set out to check
Before training or transferring any probe we had to establish, empirically, how AISI's released
lie-detector checkpoints read the model: which residual-stream layer index their `layer = L` refers to,
which token(s) they pool over, how the transcript is rendered (reasoning inside `<think>`, earlier
turns, system prompt), and how the 1 %-FPR Alpaca threshold is computed — using only the released
probes, the released rollouts, and the loader (which contains no extraction code). Gate: one convention
reproduces the checkpoints' own numbers (criteria a–e in notes/conventions.md).

## 2. What we did (plain language)
- Set up the H100 box, downloaded the base model, the 7 Qwen3.6 organisms, all probe repos, and the
  rollouts; audited the organisms' training configs; transcribed the paper's numbers and digitised
  Figure 6 from the vector PDF.
- Verified on CPU that re-rendering every stored transcript through the chat template reproduces the
  generated text token-for-token (12,658 rows, 0 failures), so teacher-forced forward passes see
  exactly what the model generated.
- Ran one GPU burst on the gender_secret_female organism: hooked every candidate layer and pooled the
  activations of the scored turn in five ways for the validation, training, calibration and auditing
  splits; then scored every released checkpoint under every candidate on CPU.
- When the DYL probes failed at every content-token pooling, dumped per-token activations around the
  yes/no answer for a few hundred rows under four renderings and scored all candidates on CPU.
- Tested four hypotheses for why the Apollo validation numbers in sweep.json differ from ours.

## 3. What we found

### Established conventions (notes/conventions.md, decisions D2–D5, D9, D11)
| item | result | evidence |
|---|---|---|
| layer index | `layer = L` is the OUTPUT of decoder layer L (HF hidden_states[L+1]; L = 63 needs a hook because transformers overwrites entry 64 with the post-norm state) | Apollo thresholds reproduce under outL only; DYL direction cosine 0.998 (outL) vs 0.85 (hsL) at L63 |
| Apollo pooling | mean over the scored turn's content tokens (after `</think>\n\n`), excluding `<|im_end|>` | stored 1 %-FPR thresholds reproduce to 3 s.f. on 22/22 checkpoints (FPR 1.01 % on our Alpaca scores) |
| DYL pooling | the single token immediately BEFORE the answer content — the "\n\n" after `</think>`, i.e. the state that generates the yes/no token | cosine with released directions 0.995 / 0.993 / 0.998 at L38/44/63; thresholds at 1.0–1.25 % FPR; stored feature mean within 0.7 % (fingerprint dim 3994 exact) |
| rendering | chat template default: earlier assistant turns without reasoning, scored turn with its reasoning; system prompt kept | preserve-reasoning cosine 0.965, no-reasoning 0.51, no-system 0.964 (all rejected); Apollo: no-system and think-block variants change nothing that matters |
| calibration | per-sample score, then 99th percentile over Alpaca rows with content | reproduces stored thresholds |
| empty-content rows | reasoning-budget exhaustion, all graded ambiguous; excluded | D9 |

### Gate criteria a–e, final (DYL at the `pred` position from the 600/600/400-row windows; Apollo from the full splits)
| criterion | DYL (outL, pred) | Apollo (outL, mean) |
|---|---|---|
| a direction cosine ≥ 0.99 | 0.995 / 0.993 / 0.998 (L38/44/63) ✓ | n/a (no released training rollouts) |
| b stored mean/std | rel. err 0.7 % / 3 %, d3994 exact; alternatives 20–70× worse ✓ (re-check on full train split in M1) | n/a |
| c metrics vs sweep.json | BA at stored threshold 0.933 vs 0.952 (default ckpt); AUROC 0.968 vs 0.982 ~ | AUROC 0.994 vs 0.982; TPR/FPR 0.957/0.014 vs 0.974/0.106 ✗ |
| d layer 63 discriminates | outL 0.998 vs hsL 0.853 / postnorm 0.982 ✓ | – |
| e calibration | FPR 1.0–1.25 % ✓ | FPR 1.01 % on 22/22 ✓ |

Verdict: the conventions are locked on a, b, d, e (DYL) and e (Apollo). Criterion c — reproducing
sweep.json's validation metrics — is NOT met for either family. The sweep used prompt-condition
labels (exactly 500 honest-condition rows − 1 and 500 of 2000 lie-condition rows, matching its 499/500
denominators), but even with those labels our honest-condition FPR is 0.2 % against their 10.6 %:
their validation rows were scored under some variant we have not identified. Hypotheses: H1 eval split
— rejected (AUROC 0.966/0.763); H4 held-out training data — untestable (no public data);
H2 system prompt removed — rejected (0.990/0.939/0.014); H3 think-block pooling — rejected
(0.990/0.933/0.013). Recorded as their unknown validation protocol (D12); sweep.json is not used as
a reference. The Apollo convention is accepted on the Alpaca calibration match.

### Other findings
- Sweep repos: 62 (paper: 55). GS-F Qwen3.6 = sweep_default_s0 (seed 0), all other organisms seed 42.
- Apollo probe grid {13,…,57}, DYL {38,…,63}; both = round(pct × 63). No dyl-honest probes.
- LoRA covers 256 modules (MLP in all 64 layers; attention only in the 16 full-attention layers).
- Figure 6 is per testbed, not per organism (docs/fig6_readings.md).
- Extraction throughput 3.1–3.4 k tok/s with the fused linear-attention kernel (reference: ≈ 2.4 k).

## 4. What it means for the project
- T0 and every transfer experiment can use the released probes as intended: Apollo = mean over content
  tokens at outL; DYL = the pre-answer position at outL after generating the follow-up reasoning.
- DYL scoring needs the follow-up REASONING generated (up to `</think>\n\n`); the answer token is
  logged for the confession-rate baseline but not needed by the probe (D11).
- sweep.json's validation numbers cannot be used as a per-checkpoint reference; the paper's Figure 6
  (per testbed) and prose medians are the M1 reference instead (revised M1 gate in CLAUDE.md).
- The run-2 DYL features (first-content-token pooling) are superseded; M1 extracts `pred`.

## 5. What we would do differently
- Dump a per-token window around the scored position from the start (cheap) instead of five fixed
  poolings; the lock would have closed in one burst.
- Treat "sweep.json = validation split, graded labels" as a hypothesis, not a fact — it cost a day.
- Install the fused kernels (and build causal-conv1d in a matching-CUDA venv) before the first burst.
- Run one process per organism over all splits (one model load), and dump only the locked
  convention's layers once it is locked.
