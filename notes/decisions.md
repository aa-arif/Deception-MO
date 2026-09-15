# Decision records

Format: context → options → decision → consequence. Referenced from notes/LOG.md as D<n>.

## D1 (2026-09-14) M0 split into CPU Phase A and GPU Phase B
Context: GPU time is metered; the convention lock needs forward passes but most of M0 is
tokenizer / checkpoint / parquet inspection. Options: (a) one interactive GPU session doing
everything; (b) CPU prep first, then a scripted burst of forward passes only. Decision: (b),
scripts/run_m0_phaseB.sh ordered by evidential value so it can be cut short. Consequence:
Phase B needs explicit go-ahead (>1 h rule); all analysis (src/m0_lock.py) runs on CPU from
cached features.

## D2 (2026-09-14) Use the base tokenizer, not the adapter repos' tokenizer.json
Context: adapter repos ship a tokenizer.json that differs from the base (merges,
pre-tokenizer regex, decoder flags, 7 extra audio/tts tokens). Options: base tokenizer;
adapter tokenizer; per-organism choice. Decision: base tokenizer. Consequence: verified
identical tokenisation on all 12,658 round-tripped rows (0 disagreements); one tokenizer
for every organism simplifies feature caching.

## D3 (2026-09-14) Layer-index candidates hsL / outL / postnorm, captured with hooks
Context: probes store `layer = L` but the loader has no extraction code; HF hidden_states has
65 entries and transformers 5.17 replaces entry 64 with the post-norm state. Options: index
the HF tuple directly; hook decoder-layer outputs. Decision: hook Qwen3_5DecoderLayer outputs
(files L{k}.npy = output of decoder layer k) and the final norm; score each probe under
hsL = L{L−1}, outL = L{L}, postnorm = Lnorm (L = 63). Prediction: outL (layer_pct formula,
threshold magnitudes). Consequence: both candidates come from one forward pass; layer 63 is
the decisive test (criterion d).

## D4 (2026-09-14) DYL answer token = first content token of the follow-up turn
Context: README says activations at the yes/no token, mean-pooled if it spans several tokens.
Options: first content token; mean over content tokens; last token; <|im_end|>. Decision:
primary = first content token (every non-ambiguous GS-F DYL row starts with a single-token
yes/no); all four poolings are stored and scored so the lock can overturn this.
Consequence: rows with empty content (all labelled ambiguous) get NaN features and are
dropped.

## D5 (2026-09-14) DYL context: first assistant turn rendered WITHOUT its reasoning
Context: the chat template drops reasoning_content for assistant turns before the last user
query unless preserve_thinking=True. Options: default template; preserve_thinking.
Decision: default template (this is how vLLM/HF chat would have generated the follow-up).
Consequence: `--preserve-thinking` extraction kept as the fallback if the lock fails.

## D6 (2026-09-14) Tolerance for reproducing sweep.json = first-500-per-class + bootstrap band
Context: sweep.json metrics are on a 500/500 subsample of the validation split (TPR/FPR in
multiples of 1/500) and the subsample is not identified. Options: demand 2-decimal match on
the full split (impossible if the subsample differs); accept any value; report the
first-500-per-class subsample plus mean ± sd over 200 random 500/500 resamples. Decision:
the last. Consequence: criterion c = within the bootstrap band; subsample-free criteria a, b
(direction cosine, stored mean/std) carry the discrimination between adjacent layers.

## D7 (2026-09-14) Storage: pooled per row only; per-token only for gender_secret @ L44/L38, fp16
Context: user directive. Options: per-token everywhere (tens of GB per split); pooled only;
pooled + targeted per-token. Decision: pooled float32 memmaps for every split (5 poolings ×
every candidate layer); per-token fp16 npz per row only for the gender_secret auditing set
at the released GS-F default layers (DYL 44, Apollo 38). Consequence: token-level analyses
(score trajectories, where in the answer the lie signal appears) are possible for
gender_secret only; anything else needs a new GPU burst.

## D8 (2026-09-14) M1 gate replaced (no per-organism numbers exist in the paper)
Context: the original gate ("±0.03 AUROC of the paper's per-organism numbers") is untestable —
Section 6.2 gives medians in prose and Figure 6 bars only. Options: keep as is; medians only;
medians + figure readings + rank correlation. Decision: (i) medians over the 7 Qwen3.6
organisms within ±0.03 of the prose medians; (ii) per-organism within ±0.05 of Figure 6 bar
readings; (iii) Spearman ≥ 0.7 between our ranking and the figure's. Consequence: Figure 6
must be digitised (pdfplumber rects if vector, else by eye) and the method recorded in
docs/cooney_numbers.md before M1's summary.

## D9 (2026-09-15) Empty-content rows are excluded everywhere
Context: 0.8–3 % of rows per split have reasoning but no content (generation budget exhausted);
graders label them ambiguous (Alpaca: honest by construction). Options: (a) exclude; (b) score the
reasoning tokens instead; (c) assign the minimum score. Decision: (a) — NaN features, excluded from
all metrics and from Alpaca calibration, counts reported. Consequence: n differs from the released
denominators (e.g. 485 vs 499 honest-condition rows in VD validation); documented in
notes/conventions.md; revisit if the released pipeline turns out to score empties (H3 test).

## D10 (2026-09-15) Lock failure handled by targeted diagnostics, not by a full re-extraction
Context: gate a–e failed; Apollo Alpaca calibration reproduces under outL/mean (so the pipeline is
sound) while validation metrics and all DYL criteria do not. Options: (a) stop and wait for the user;
(b) re-extract every split under new hypotheses (hours of GPU); (c) dump per-token windows for a few
hundred rows per hypothesis (< 1 h GPU) and test every candidate on CPU. Decision: (c), two jobs
(scripts/run_m0_followup_gpu.sh, run_m0_followup_gpu2.sh). Consequence: the lock decision moves to
CPU analysis over results/m0/dyl_tail/*; M1 stays blocked until a–e pass.

## D11 (2026-09-15) DYL readout = outL residual at position c−1 (answer-prediction position), default rendering
Context: the released DYL probes did not reproduce at any content-token pooling; per-token windows
(src/m0_dyl_tail.py) tested 15 positions × 4 renderings × 3 layer conventions. Options: first content
token (README's literal "answer token"); the token before it; </think>; turn-start tokens; content
means; each under default / preserve-earlier-reasoning / no-reasoning / no-system renderings.
Decision: **outL residual at c−1 = the last token before the answer content (the "\n\n" after
`</think>`), i.e. the position whose next-token prediction is the yes/no token, under the default
chat-template rendering** (earlier assistant turn without its reasoning, follow-up turn with its
reasoning). Evidence: cos ≥ 0.993 with released `dim` directions at L38/44/63, stored thresholds at
1.0–1.25 % FPR on Alpaca, stored dataset_mean within 0.7 % (d3994 exact), BA within 0.02 of
sweep.json; every alternative ≤ 0.54 cosine or uncalibrated. Consequence: DYL scoring needs the
follow-up turn's REASONING to be generated (the readout sits after `</think>\n\n`) but NOT the
answer token itself — the probe reads the state that is about to emit it. All DYL-family features are
extracted with pooling `pred`; run-2 `first`-token DYL features are superseded. Recorded in
notes/conventions.md.

## D12 (2026-09-15) Apollo convention accepted on the Alpaca calibration match; sweep.json validation numbers not a reference
Context: under outL + mean-over-content-tokens the released Apollo thresholds reproduce to 3 s.f. on
22/22 checkpoints (1.01 % FPR on our Alpaca scores), but sweep.json's validation metrics do not
(our TPR/FPR 0.957/0.014 vs 0.974/0.106). Four hypotheses (eval split, no system prompt, think-block
pooling, held-out training data) failed or were untestable; labels are prompt-condition (500 − 1 /
500 of 2000). Options: (a) keep searching; (b) accept on calibration and move on; (c) retrain Apollo
probes ourselves. Decision: (b), per user directive. Consequence: M1 T0 is checked against Figure 6
(per testbed) and the prose medians, never against sweep.json; the mismatch is documented as "their
validation protocol, unknown"; if a reproducing rendering is ever found, T0 is additionally reported
under it without changing our protocol.

## D13 (2026-09-15) M1 gate (ii) = per testbed, within 0.05 or 2 SE of the Figure 6 bar, whichever is larger
Context: Figure 6 has per-testbed bars with SE across organisms (and pools Qwen3.5 + 3.6); the
original "per organism ±0.05" is not evaluable. Options: strict ±0.05 per testbed; ±0.05 or 2 SE;
skip (ii). Decision: within 0.05 or 2 SE, whichever is larger, per testbed; (iii) Spearman is
uninformative at n = 3 testbeds and is reported without a threshold. Consequence: M1 T0 Apollo PASSES
(AuditBench Δ +0.002/−0.017, Maths Sandbagger −0.005/+0.023, Gender Secret −0.090/−0.065 vs SE
0.124/0.068); Gender Secret is PROVISIONAL until the Qwen3.5 replication (M7) shows whether the bar's
height comes from the 3.5 organisms.

## D14 (2026-09-15) LoRA merging: permitted going forward, never mixed within a comparison
Context: merging the adapter into the weights gives 1.44× throughput; merged vs unmerged features
differ by ≈ 1.5 % max (2× the intrinsic bf16 batch noise) and change no probe decision, but do not
meet the strict floor. Options: restart M1 merged; finish unmerged; allow merged later. Decision: M1
(pass A + B) finishes UNMERGED; the merged path is permitted for later bursts, but merged and unmerged
features are never mixed inside one comparison (a transfer matrix, a ladder rung, a T-experiment).
Consequence: the M7 sweep run (55+ adapters) must re-extract sweep_default_s0 (= GS-F) merged
alongside the other seeds rather than reuse the unmerged M1 GS-F features; every features/meta.json
records merge_lora, and analysis scripts must assert a single value per comparison.
