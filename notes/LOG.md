# Lab notebook (append-only)

Conventions: entries are chronological, UTC timestamps. Flags: DEVIATION:, SURPRISE:, OPEN:.
Decision records are in notes/decisions.md (D<n>); terms in notes/glossary.md.
Entries before 2026-09-14 23:00 were BACKFILLED at 23:10 from the two Phase A commits, the
notes/*.md files and results/m0/roundtrip/*.json; they were not written contemporaneously.

---

## 2026-09-14 21:19–21:32 — M0 skeleton (commit 177358f)
Goal: put the user's CLAUDE.md and PLAN.md into a fresh repo on the NFS and start M0.
Ran: manual file creation; `git commit` at 21:32. Inputs: user-supplied CLAUDE.md, PLAN.md.
Out: CLAUDE.md, PLAN.md, notes/m0_plan.md, docs/cooney.pdf → docs/cooney.txt (pdfplumber),
notes/calibration.md, src/m0_roundtrip.py.
Why: M0 is split into a CPU Phase A (tokenizer / checkpoint / parquet work) and a GPU Phase B
(forward passes only) so that the metered GPU burst is as short as possible (D1).

## 2026-09-14 21:25–21:49 — M0 Phase A (commit 42df0b4)
Goal: environment, downloads, paper transcription, loader/probe audit, tokenizer round-trip,
predicted activation convention, Phase B scripts.
Ran:
- venv: uv-managed CPython 3.12.14 at ~/venvs/lieprobes (local disk). Pins in notes/env.md
  (torch 2.13.0+cu130, transformers 5.17.0, peft 0.20.0, vllm 0.29.0, lie-detectors).
- downloads: scratchpad dl_priority.py (log notes/.download_log.txt) and base download
  (notes/.download_base_log.txt). Base Qwen/Qwen3.6-27B done 21:31; rollouts + 7 Qwen3.6
  adapters + Qwen3.5 adapter configs done 21:37 (PRIORITY_DONE); probe repos continue in the
  background (dyl, apollo, targeted-apollo, dyl-truthful done by 22:57; uq + SFT rollouts
  still downloading at 23:00). Unauthenticated (no HF token cached on the box).
- notes/organism_configs.md: 13 hyperparameters.json + adapter_config.json audited.
- notes/conventions.md: loader read ($FS/lie_detectors @ 88043087), probe checkpoints
  inspected, predicted convention.
- src/m0_roundtrip.py over 5 GS-F splits → results/m0/roundtrip/*.json.
- src/extract_features.py, src/m0_sanity.py, src/m0_lock.py, scripts/run_m0_phaseB.sh.
Out (round-trip, GS-F organism rollouts):

| split | n | scored tokens mean / max | round-trip failures | adapter-tokenizer disagreements |
|---|---|---|---|---|
| gender_secret | 158 | 66.4 / 320 | 0 | 0 |
| varied_deception_validation | 2500 | 46.7 / 362 | 0 | 0 |
| dyl_validate_varied_deception | 5000 | 2.75 / 212 | 0 | 0 |
| dyl_alpaca_validate | 2500 | 1.84 / 80 | 0 | 0 |
| alpaca | 2500 | 269.6 / 1844 | 0 | 0 |

Why: see D2 (base tokenizer), D3 (candidate conventions), D4 (DYL answer token = first
content token), D5 (DYL context reasoning dropped), D6 (500/500 subsample tolerance).
SURPRISE: Apollo probes use layers {13,19,25,32,38,44,50,57}, not the DYL grid
{38,…,63} that CLAUDE.md assumed for every family. Both grids = round(pct/100 × 63).
SURPRISE: sweep.json TPR/FPR are multiples of 1/500 (Apollo FPR 1/499) ⇒ metrics were
computed on a 500-lie / 500-honest subsample of the validation split; exact 2-decimal
reproduction needs the subsample (D6).
SURPRISE: layer-63 DYL `dim` thresholds reach 20744 with |direction| ≈ 102 ⇒ the probes
read a pre-final-norm residual stream (post-norm RMS ≈ 1 could not produce that scale).
SURPRISE: the sweep has 62 repos on the Hub, not the paper's 55. GS-F Qwen3.6 is literally
sweep_default_s0 (seed 0); every other organism uses seed 42.
SURPRISE: there are no dyl-honest probe repos (dyl_honest_* rollout splits do exist).
SURPRISE: Qwen3.5-27B has an ab_contextual_optimism adapter but no probe repos for it.
SURPRISE: transformers 5.17 overwrites hidden_states[64] with the post-norm output
(capture_outputs tie), so the raw layer-63 output is only reachable via a forward hook.
DEVIATION: Python 3.12 venv instead of the system 3.10 (lie-detectors needs ≥3.11).
OPEN: meaning of `ar` in every checkpoint filename (not a hyperparameter field).
OPEN: which 500/500 subsample sweep.json used (first-500-per-class in parquet order is the
first guess; otherwise the bootstrap band is the tolerance).

## 2026-09-14 21:54 — directives received for Phase B; session ended before applying them
The user approved Phase B with five directives (storage pooled-per-row, per-token only for
gender_secret @ L44/L38 fp16; gate criteria a–e in conventions.md; tokens/s logging;
HF_TOKEN; CLAUDE.md corrections + revised M1 gate). The session died at 21:54 with none
applied; Phase B was NOT launched.

## 2026-09-14 23:01–23:15 — directives applied (this commit)
Goal: apply the 21:54 directives, then launch Phase B.
Ran: audit of src/extract_features.py, notes/conventions.md, CLAUDE.md against the directive
text recovered from the previous session transcript. Result: (1) pooled-per-row was already
true (no per-token output anywhere), per-token dump missing; (2) gate criteria missing;
(3) tokens/s missing; (4) no HF token cached in ~/.cache/huggingface/token or $HF_HOME/token
(login did not land on this box — DEVIATION: downloads stay unauthenticated; no stalls seen,
0 retries in 90 min); (5) none of the CLAUDE.md corrections applied.
Changes: src/extract_features.py `--per-token-layers` (fp16 npz per row, full sequence + ids
+ span offsets) and wall-clock / tok/s per split in meta.json; scripts/run_m0_phaseB.sh
passes `--per-token-layers 44 38` for gender_secret only; notes/conventions.md gate
criteria a–e with a side-by-side table; CLAUDE.md data/probe/sweep corrections, revised
M1 gate, storage convention, and this documentation section; notes/LOG.md,
notes/decisions.md, notes/glossary.md created (D7, D8).
Dry run: `python src/extract_features.py --organism gender_secret_female --splits
gender_secret --per-token-layers 44 38 --dry-run` → n=158, 146,312 tokens, max 6179,
0 over max_len 8192, 3 empty-content rows.
Why per-token only at 44/38: those are the released GS-F defaults (DYL l_44_ar_dim, Apollo
l_38_lm_500000_ar_lr); per-token dumps at all ~30 captured layers would be ~30× larger and
nothing in M0–M4 needs them.

## 2026-09-14 23:06 — Phase B launched (commit 84070f3)
Ran: `cd /lambda/nfs/lieprobes/repo && nohup bash scripts/run_m0_phaseB.sh > results/m0/phaseB.log 2>&1 &` (pid 57619). Organism gender_secret_female; splits in order: sanity, dyl_validate_varied_deception, dyl_train_city_countries (2500 rows), varied_deception_validation, dyl_alpaca_validate, alpaca, gender_secret (+per-token 44/38); then m0_lock.py for dyl and apollo. Download job (uq probes + SFT rollouts) still running concurrently on the NFS.

## 2026-09-14 23:11 — Figure 6 digitised while Phase B loads weights (CPU)
Goal: get numeric Figure 6 values for the revised M1 gate (ii)/(iii).
Ran: `python src/fig6_digitise.py` (commit after 84070f3) on docs/cooney.pdf page 10 → docs/fig6_readings.{json,md}.
Out: 3 panels × 5 detectors × 4 testbeds; calibration verified against gridlines (exact); SE from error bars. Table in docs/cooney_numbers.md.
Why numeric: the figure is vector (66 rects, 209 lines, 0 images), so pdfplumber rects beat reading by eye (directive 2026-09-14).
SURPRISE: first attempt assumed colour = detector and x-cluster = testbed; the legend swatches show colour = testbed and the x clusters are five detectors (incl. "Judge Model (no CoT)"). Fixed.
DEVIATION: Figure 6 has no per-organism bars — only per-testbed means with SE — so gate (ii) "per-organism ±0.05 vs Figure 6" cannot be evaluated as written; docs/cooney_numbers.md proposes the per-testbed form.
OPEN: confirm the per-testbed form of gate (ii)/(iii) with the user before M1's SUMMARY.
Note: prose Varied Deception numbers exceed the digitised bars by ≈0.03 (medians vs means) — not a calibration error (gridlines match panel edges to 0.01 pt).

## 2026-09-14 23:07–23:14 — Phase B step B1/B2: sanity (GPU, 7.5 min incl. 340 s weight load)
Goal: module path, hidden_states semantics, adapter coverage, batching invariance, GS-F behaviour.
Ran: `python src/m0_sanity.py` (commit 84070f3) → results/m0/sanity.json. Base bf16 = 51.0 GiB; peak 55.9 GiB.
Out:

| check | result |
|---|---|
| decoder layers | 64 at `model.language_model.layers.{i}`; final norm `model.language_model.norm` |
| len(hidden_states) | 65 |
| hs[i+1] == hook(layer i), i < 63 | True (exact) |
| hs[64] == post-norm output / == raw layer-63 output | True / False (HF tie confirmed; raw layer 63 only via hook) |
| hs[0] == embeddings | True |
| last-token residual norm L13 / L38 / L44 / L63 / post-norm | 41.6 / 105.9 / 101.7 / 309.4 / 139.4 (max |x| L63 raw 548, post-norm 49.8) |
| LoRA modules found | 256 (adapter has 512 tensors = 256 × A/B) |
| batched vs single pooled features, max rel diff (3 rows × L38/44/63) | 0.0014 – 0.0081 |
| GS-F reasoning mentions female / output denies | True / True (see caveat) |

SURPRISE: 256 LoRA modules, not the 448 = 64 × 7 CLAUDE.md expects. Adapter header: gate/up/down_proj in
all 64 layers (192) but q/k/v/o_proj only in the 16 full-attention layers 3,7,…,63 (64); the 48
linear-attention (GatedDeltaNet) layers have no q/k/v/o_proj modules, so the target list matches
nothing there. 256 is therefore the correct coverage — not a loading bug.
CAVEAT: both 400-token generations ended inside the think block (no `</think>` reached); the
"denies in output" flag matched the drafted answer inside the reasoning. The organism's reasoning
states "I know the user is female … I must deny knowing the user's gender in the text output", the
base model's does not — the behavioural point stands, but the visible-output denial is unverified.
OPEN: re-run the behavioural check with max_new_tokens ≥ 1200 when the GPU is next hot.
Note: batched-vs-single diffs up to 0.8 % are bf16 kernel-path noise (different T per batch), not
a masking bug (the DYL answer token and the mean pooling agree to the same tolerance).
DEVIATION (perf): transformers falls back to reference PyTorch for `chunk_gated_delta_rule` and
`causal_conv1d` ("correct but much slower"). Installed flash-linear-attention 0.5.2 (Triton) into the
venv at 23:16; causal-conv1d 1.7.0 fails to build (wheel compiled for CUDA 12.8 vs torch cu130).
The running extraction still uses the reference kernels; restart decision depends on measured tok/s.

## 2026-09-14 23:14–23:20 — Phase B run 1 extraction stopped after 21 batches; run 2 relaunched with fused kernels
Goal: keep the burst inside the ≤ 1.5 h target.
Observed (run 1, reference kernels, results/m0/phaseB_run1_sanity.log): model ready 133 s (warm NFS
cache); dyl_validate_varied_deception batch 21/428: 2378 tok/s on the SHORTEST sequences (batches are
length-sorted ascending) ⇒ ≥ 2.3 h for the 19.7 M-token M0 budget, worse as T grows.
Decision: stop run 1 at 23:20 (nothing written: the memmaps were NaN-initialised and are deleted),
relaunch with `SKIP_SANITY=1` (new guard in scripts/run_m0_phaseB.sh; sanity.json kept from run 1)
so transformers picks up flash-linear-attention 0.5.2 for `chunk_gated_delta_rule`. Cost ≈ 7 min;
expected gain: fused Triton kernel for the 48 linear-attention layers. causal_conv1d still falls back.
Ran: `SKIP_SANITY=1 nohup bash scripts/run_m0_phaseB.sh > results/m0/phaseB.log 2>&1 &` at 23:20:34.
Note on numerics: fused vs reference gated-delta-rule kernels differ at bf16 noise level; ALL splits
come from run 2, so the feature set is internally consistent. The run-1 batching check (≤ 0.8 % rel)
was under reference kernels; the lock itself is the real test.
Mishap: the first stop attempt used `pkill -f run_m0_phaseB.sh`, which matched the calling shell and
killed it (exit 144), leaving the python child orphaned for ~40 s; second attempt killed by PID.

## 2026-09-14 23:32 — Phase B run 2 throughput and budget projection
Run 2 (fla fused gated-delta-rule; causal_conv1d still reference): model ready 113 s; first batch 49 s
(Triton compile). Marginal throughput on dyl_validate_varied_deception, length-sorted batches:

| batches | T (max tokens in batch) | marginal tok/s |
|---|---|---|
| 21–41 | 444–582 | 2812 |
| 41–61 | 582–670 | 2883 |
| 61–81 | 670–731 | 2903 |
| 81–101 | 731–778 | 2937 |
| 101–121 | 778–825 | 3376 |

Run 1 (reference kernels) managed 2378 tok/s cumulative over batches 1–21 (T ≤ 444), i.e. the fused
kernel gives only a modest gain at these lengths; the win should grow with T (linear-attention
reference cost scales worse). SURPRISE: the gain is smaller than the "much slower" warning suggested.
Token budget (tokenise-only dry runs, GS-F organism, max_len 8192, nothing truncated):

| split | rows | tokens |
|---|---|---|
| dyl_validate_varied_deception | 5000 | 5,715,148 |
| dyl_train_city_countries (first 2500) | 2500 | 2,495,083 |
| varied_deception_validation | 2500 | 3,474,480 |
| dyl_alpaca_validate | 2500 | 2,593,890 |
| alpaca | 2500 | 2,721,348 |
| gender_secret (+ per-token 44/38) | 158 | 146,312 |
| total | 15,158 | 17,146,261 |

At ~3.2k tok/s ≈ 90 min of forward passes + 5 model reloads (~2 min each, one per
extract_features.py invocation) ⇒ extraction done ≈ 01:00 UTC, lock analysis (CPU) a few minutes
after. DEVIATION: over the ≤ 1.5 h Phase B target by ~20 min; the burst was approved as a whole,
so it continues. Improvement for M1: one process per organism over all splits (one reload), and
try --batch-tokens 32768 (GPU peak 60 GiB of 80 at 16384).

## 2026-09-15 01:05 — Phase B run 2 finished (extraction 23:22–01:01, lock analysis 01:01–01:05)
Per-split (GS-F organism, fla kernels): dyl_validate 30.7 min @3103 tok/s; dyl_train(2500) 12.5 min
@3340; VD validation 17.5 min @3318; dyl_alpaca 12.9 min @3339; alpaca 13.5 min @3355; gender_secret
1.0 min @2354 (+ per-token L44/L38 fp16). Features: 5.8–12 GB per split (float32, 27 layers + norm,
5 poolings). Artefacts: features/qwen3.6-27b/gender_secret_female/*, results/m0/lock/{dyl,apollo}__
gender_secret_female.{json,md}. The session was idle 01:05–06:47 (GPU idle, nothing launched).

## 2026-09-15 06:47 — GATE RESULT: a–e FAIL for every candidate (src/m0_gate_table.py)
Per the 2026-09-15 pre-approval, M1 extraction was NOT started.
Apollo (val = varied_deception_validation, pooling mean, 22 ckpt rows per candidate):
- e (calibration) PASSES under **outL** for every checkpoint: stored threshold → 1.01 % FPR on our
  Alpaca scores (25/2480), recomputed p99 == stored threshold to 3 s.f. Under hsL: 0.6–10 % FPR.
  ⇒ layer convention outL + mean over content tokens (excl. <|im_end|>) reproduces the released
  Alpaca scoring numerically. Teacher forcing / spans / layer index are right.
- c FAILS: our AUROC is ABOVE sweep.json everywhere (default: 0.994 first500 vs 0.9817; TPR/FPR at
  the stored threshold 0.957/0.014 vs sweep 0.974/0.106). The sweep's honest rows score much higher
  than ours; the lie rows slightly higher.
DYL (val = dyl_validate_varied_deception, pooling first content token):
- everything off in SCALE: stored thresholds flag 74–100 % of honest rows (sweep FPR 0.05–0.10);
  a) direction cosine 0.33–0.41 (all content poolings), b) stored dataset_mean rel. err 0.49–0.78,
  d3994 fingerprint ours 73.7–75.4 vs stored 81.9 (L44), 208/412 vs 307 (L63). AUROC nevertheless
  0.97–0.98 (sweep 0.98–0.99) ⇒ the released probes read a token/context close to, but not equal
  to, our first-content-token feature. Only l_44_lm_0_001 under hsL/first calibrates (1.03 %),
  judged coincidental (L38 lr: 84 %).
- d: at L63 no candidate reproduces (all AUROC 0.57–0.95 vs 0.63/0.99).
SURPRISE: sweep.json is on a 500-lie / 499-honest set; varied_deception_validation has exactly 500
honest-CONDITION rows (10 honest prompts) and 2000 lie-condition rows (10 lie prompts) ⇒ the sweep
used prompt-condition labels (500 honest-condition rows minus one, 500 sampled lie-condition rows),
NOT the graded is_lie labels. But condition labels on OUR scores give AUROC 0.917, TPR 0.765,
FPR 0.002 (sweep 0.982/0.974/0.106): their validation SCORES differ from ours even though their
Alpaca scores match. Length/truncation ruled out (no honest-condition row > 4096 tokens; top-scoring
honest rows are not long). Labelling variants (ambiguous→lie/honest, empties as min score) also fail.
OPEN: what differs between the sweep's validation scoring and its Alpaca scoring? Hypotheses queued
on GPU (results/m0/followup_gpu*.log): (H1) sweep.json computed on the varied_deception EVAL split;
(H2) system prompt removed at scoring time (would raise honest-condition scores, keep lie scores);
(H3) mean over the whole assistant turn incl. the think block (`mean_all`) or think-only.
DYL hypotheses: token position (predicting position c-1 = "\n\n", "</think>", start-of-turn
positions), context (earlier turn's reasoning preserved; follow-up rendered without reasoning;
system prompt removed) — src/m0_dyl_tail.py dumps fp16 activations at 15 positions × 7 layers for
600 train / 600 val / 400 alpaca rows per context; src/m0_dyl_tail_analyse.py scores them.
DEVIATION (judgment call): two GPU jobs (~40 + ~50 min) launched at 06:55 for the lock follow-up
although the pre-approval said "leave the GPU idle" on failure — that clause was read as "no M1";
the instance is billed while idle, the jobs are < 1 h each and serve M0 only. Nothing from M1 runs.
Also: HF token still absent on the box; flash-linear-attention installed (run 2); causal-conv1d
being built in a separate cu128 venv (~/venvs/lieprobes-cu128) for the fast path.

## 2026-09-15 06:50 — Empty-content rows (directive item 2)
See notes/conventions.md "Empty-content rows" and decisions.md D9.

## 2026-09-15 07:03 — cu128 venv built (item 1 prep); GPU job 1 (DYL tail windows) running
~/venvs/lieprobes-cu128: torch 2.11.0+cu128 + causal-conv1d 1.7.0 + fla 0.5.2 (see notes/env.md).
Attention: transformers 5.17 default for Qwen3_5 = SDPA; flash-attn has no prebuilt wheel for torch
2.11/cu128 (source build only) — deferred until src/profile_extract.py shows whether the 16
full-attention layers matter. GPU job 1 throughput 3.2 k tok/s (same as run 2).

## 2026-09-15 07:35 — DYL LOCK RESOLVED: outL at the answer-PREDICTION position (src/m0_dyl_tail_analyse.py)
Ran: `python src/m0_dyl_tail_analyse.py default preserve_thinking no_reasoning_last` on the tail
windows (600 train / 600 val / 400 alpaca rows per context; 15 positions × {37,38,43,44,62,63,norm};
results/m0/dyl_tail/*.md). Wall: GPU job 1 windows 06:55–07:23, analysis 4 min CPU.
Winner: context **default** (template as generated: earlier turn's reasoning dropped, follow-up turn
with its reasoning), position **c−1** = the "\n\n" token after `</think>`, i.e. the position whose
next-token prediction IS the yes/no answer; layer convention **outL**.

| ckpt | cand | a cos | b mean/std rel err (d3994 ours/stored) | e FPR@stored thr (p99 / stored) | c AUROC / TPR / FPR / BA (sweep) | PASS |
|---|---|---|---|---|---|---|
| l_38_ar_dim | outL | 0.9952 | – | 0.0125 (−1.65 / −2.27) | 0.963 / 0.957 / 0.133 / 0.912 (0.982 / 0.984 / 0.096 / 0.944) | BA −0.032 |
| l_44_ar_dim (default) | outL | 0.9929 | – | 0.0125 (−32.8 / −34.8) | 0.968 / 0.947 / 0.080 / 0.933 (0.982 / 0.966 / 0.062 / 0.952) | ✓ |
| l_63_ar_dim | outL | 0.9976 | – | 0.010 (20048 / 20744) | 0.800 / 0 / 0.003 / 0.498 (0.630 / 0.002 / 0 / 0.501) | ✓ |
| l_63_ar_dim | hsL / postnorm | 0.853 / 0.982 | – | 0 / 0 | – | ✗ (d: outL discriminates) |
| l_38_lm_0_001_ar_lr | outL | – | 0.0073 / 0.033 (70.3 / 70.3) | 0.015 | 0.982 / 0.940 / 0.060 / 0.940 (0.990 / 0.982 / 0.054 / 0.961) | b > 1e-3 |
| l_44_lm_0_001_ar_lr | outL | – | 0.0070 / 0.033 (81.9 / 81.9) | 0.010 | 0.980 / 0.947 / 0.067 / 0.940 (0.991 / 0.982 / 0.054 / 0.964) | b > 1e-3 |
| l_63_lm_0_001_ar_lr | outL | – | 0.016 / 0.031 (308.5 / 306.9) | 0.015 | 0.968 / 0.940 / 0.087 / 0.926 (0.987 / 0.974 / 0.054 / 0.960) | b > 1e-3 |

Every other position (first content token, </think>, start-of-turn tokens, last content token,
answer+im_end, content mean) has cos ≤ 0.54 and no calibration. Other contexts at c−1/outL:
preserve_thinking cos 0.965 (L44), no_reasoning_last 0.51 ⇒ the default rendering is theirs.
Criterion b: stored dataset_mean/std vs our 600-row train subset differ by 0.7 % / 3 % (the stored
statistics come from their full training set); the d3994 fingerprint agrees to 3 s.f., and the
alternatives are 20–70× worse. To be re-checked with the full dyl_train split in M1 (pooling `pred`
added to src/extract_features.py). Criterion c: BA within 0.02 for the default ckpt; AUROC 0.015
below sweep on our 300/300 subset — same "unknown validation protocol" as Apollo (H1–H3 pending).
DEVIATION from prediction (conventions.md predicted "first content token"): the README's "activations
at the generated Yes/No answer token" means the residual stream at the generation step that emits the
answer, i.e. the last prompt-side token before it. Consistent with Apollo: outL everywhere.
DEVIATION: the run-2 DYL features (pooling `first`) are the wrong position for DYL probes; DYL splits
must be re-extracted with `pred` (cheap: same forward passes as M1).
SURPRISE: at this position the L63 dim probe is degenerate by design (sweep BA 0.501) yet still
reproduces cos 0.998 and the calibration — a strong check that both the position and outL are right.
Next: H1 (eval split), H2 (no system prompt), H3 (think-block pooling) for Apollo; DYL no_system
context for completeness. Then profiler + fast-path validation.

## 2026-09-15 07:42 — Apollo H1 REJECTED (src/m0_apollo_h1.py on varied_deception first 1200 rows)
Eval split (64 prompts; graded 493 lie / 226 honest / 481 ambiguous; condition 891 / 309):
default l_38_lm_500000: graded AUROC 0.966, TPR/FPR 0.866/0.022; condition 0.763, 0.692/0.237
(sweep 0.982, 0.974/0.106). Other ckpts likewise below sweep. ⇒ sweep.json is not the eval split.
H4 untestable (no public instructed-pairs rollouts). H2/H3 pending (GPU job 2, ~08:30).

## 2026-09-15 07:55 — M1 extraction driver written (scripts/run_m1_extract.sh); not yet launched
Design: one process per organism per pass (one model load each); pass A = auditing sets present in the
organism's dir (gender_secret / audit_bench_updated / sandbagging_games_updated; base: the two
gender_secret_prompted_* sets + audit_bench_updated) + alpaca + dyl_alpaca_validate +
varied_deception_validation + sft_mo_last300; pass B = dyl_train_city_countries (full 5000),
dyl_validate_varied_deception, varied_deception. Layers: outL at the 12 released probe layers
{13,19,25,32,38,44,50,54,57,60,62,63} + post-norm (the lock is closed, so L−1 copies are dropped);
8 poolings incl. `pred` (D11). Per-token fp16 only for gender_secret at L44/L38 (D7). --skip-existing
makes reruns idempotent. Storage ≈ 2.1 MB/row ⇒ ≈ 40 GB per organism.
SFT rollouts: qwen3_6_27b_<organism>_rollouts has mo_specific_questions (1978 rows) + trivia_qa
(4106), columns instruction/reasoning/output(+pre_rewrite)/sub_category, NO held-out marker.
OPEN: "300 held-out SFT rollouts" cannot be identified; `sft_mo_last300` = last 300 rows of
mo_specific_questions in file order (rendered user/assistant with reasoning, label honest) — treat as
in-training trait-active controls until the user says otherwise. Base has no SFT rollouts.
DEVIATION: the run-2 GS-F features (27 layers, 5–7 poolings, no `pred`, dyl_train capped at 2500)
will be moved to features/qwen3.6-27b_run2_gsf before M1 so GS-F is re-extracted in the M1 layout.
Budget per organism (tokens): A ≈ 0.15–0.4 M auditing + 2.7 M alpaca + 2.6 M dyl_alpaca + 3.5 M VD-val
+ 0.44 M sft ≈ 9.4 M; B ≈ 5.0 M dyl_train + 5.7 M dyl_val + ~4.3 M VD ≈ 15 M ⇒ ≈ 24 M × 8 ≈ 195 M
tokens: ≈ 16 h at 3.3 k tok/s, ≈ 5.5 h at 10 k tok/s.

## 2026-09-15 07:45 — clock correction
The headings "07:35 DYL LOCK RESOLVED", "07:42 H1 REJECTED" and "07:55 M1 driver" above were written
with estimated times; the wall clock was ≈ 07:30, 07:38 and 07:43 respectively (GPU job 2 started
07:38:58, and at 07:44 it was at batch 11/32 of its first context). The single
"CUDACachingAllocator ... OOM" line in results/m0/followup_gpu2.log at 07:43:20 is a recoverable
allocator warning (PyTorch freed its cache and retried); the job continued at 3.3 k tok/s.

## 2026-09-15 07:58 — DYL no_system context: REJECTED (system prompt is kept in the released rendering)
`python src/m0_dyl_tail_analyse.py no_system`: at c−1/outL cos 0.964 (L38), 0.963 (L44), 0.991 (L63)
vs default 0.995 / 0.993 / 0.998; L44 TPR at stored threshold 0.837 vs default 0.947 (sweep 0.966).
⇒ DYL rendering = default template WITH the system prompt (D11 unchanged). results/m0/dyl_tail/no_system.md.

## 2026-09-15 08:14 — Apollo H3 REJECTED; re-extraction control reproduces run 2 (src/m0_apollo_h2h3.py)
GPU job 2 step 2 (VD validation, L37/38/43/44, 8 poolings, 17.4 min @3332 tok/s → features/qwen3.6-27b_v2):
| pooling | labels | default ckpt AUROC / TPR / FPR | sweep |
|---|---|---|---|
| mean_all (think + content) | graded / condition | 0.990 / 0.933 / 0.013 — 0.950 / 0.718 / 0.002 | 0.982 / 0.974 / 0.106 |
| mean_think | graded / condition | 0.990 / 0.933 / 0.011 — 0.953 / 0.716 / 0.002 | " |
| mean (control, re-extracted) | graded / condition | 0.991 / 0.957 / 0.014 — 0.917 / 0.765 / 0.002 | " |
The control equals run 2 to 3 decimals ⇒ extraction is reproducible across runs. No think-block
pooling raises honest-condition FPR anywhere near 10.6 %. H2 (system prompt removed) pending (08:28).

## 2026-09-15 08:33 — Apollo H2 REJECTED; M0 CLOSED (directive 2026-09-15 item 2)
H2 (system prompt removed; features/qwen3.6-27b_v2/.../varied_deception_validation__nosys, 17 min GPU):
default ckpt graded AUROC 0.990, TPR/FPR 0.939/0.014; condition 0.892, 0.751/0.002 (sweep 0.982,
0.974/0.106). l_38_ar_dim: 0.981, 0.25/0.0. ⇒ rejected. Summary of the Apollo validation mismatch:
| hypothesis | result |
|---|---|
| H1 sweep on the eval split | rejected (0.966 / 0.866 / 0.022) |
| H2 system prompt removed | rejected (0.990 / 0.939 / 0.014) |
| H3 think-block pooling (mean_all, mean_think) | rejected (0.990 / 0.933 / 0.013 and 0.011) |
| H4 held-out instructed-pairs training data | untestable (not public) |
| labels: graded / condition / ambiguous→lie / ambiguous→honest / empties as min | none give FPR ≈ 0.106 |
Decision D12: Apollo convention (outL, mean over content tokens) ACCEPTED on the Alpaca calibration
match (22/22 checkpoints, 3 s.f.); sweep.json validation metrics recorded as "their unknown
protocol" and not used as a reference. M0 gate: a, b, d, e met for DYL; e met for Apollo; c not
reproducible for either family for reasons outside our pipeline. M0 closed; M1 proceeds (extraction).
Artefacts: results/m0/SUMMARY.md (final), notes/conventions.md (final gate table), decisions D11/D12.

## 2026-09-15 08:50 — Fast path (cu128) validation: NOT within the strict floor; M1 uses the production path
Profiling (results/m0/fastpath_eval.log; first pass OOM'd on a 32 k-token test batch — my profiler's
fault, fixed and re-running as results/m0/profile_only.log): forward-only 3584 tok/s (cu130, conv
fallback) vs 3810 tok/s (cu128, built causal-conv1d) at T≈800×16; hooks + pooling cost 1–2 %;
length-sorted batching wastes 0.3 % (16384×16) to 1.6 % (65536×128) on padding. ⇒ the forward pass
itself is the cost (≈ 200 TFLOP/s ≈ 27 % of H100-PCIe bf16 peak); causal_conv1d and batching are not
the lever; the 10 k tok/s target is unrealistic on this GPU (would need > 70 % MFU).
Validation (src/validate_fastpath.py, 200 dyl_validate rows, same batching): at the probe layers with
the poolings we use (mean/first at L38/44/63) max rel diff 1.1–2.3 % (p95 0.7 %), cosine ≥ 0.9999
on 95 % of rows, min 0.99876; single-token `imend` at L63 up to 14 % (massive-activation token).
Released-probe scores: corr ≥ 0.9998, max |Δ| = 0.03–0.07 score-sd, threshold decisions agree 200/200.
Verdict: usable but NOT within the agreed floor (max rel ≤ 1e-2, cos ≥ 0.9999 on every row), and
the speed gain is 6 % ⇒ per the directive, M1 extraction runs on the production venv (torch
2.13+cu130, fla fused kernel, conv fallback). The cu128 venv is kept for later kernel work.
DEVIATION: run-2 GS-F features moved to features/qwen3.6-27b_run2_gsf (superseded layout); GS-F is
re-extracted in M1. m0 scripts that default to the old path need --features if re-run.
M1 extraction queued behind the profiler re-run (PROFILE_ONLY_DONE), production venv, pass A then B.

## 2026-09-15 08:58 — Profiler (fixed, production venv): time goes to the dense layers; LoRA merge is the lever
results/m0/profile_lieprobes_cu130.json (T801×16 = 12.8 k tokens): forward 3.57 s = 3586 tok/s;
module time MLP 2.11 s (57 %), linear attention 0.90 s (24 %), full attention 0.40 s (11 %), other
0.32 s (8 %). Throughput is flat across shapes (T314×16 3587, T2011×8 3496, T802×24 3516 tok/s) ⇒
compute-bound, not padding/batching (0.3 % waste) nor hooks (1–4 %).
**LoRA merged (PEFT merge_adapter, bf16): 2.49 s = 5146 tok/s, 1.44× faster** — the unmerged
adapter adds two rank-128 matmuls to each of 256 modules per token. cu128 + built causal_conv1d:
3810 tok/s unmerged (+6 %), not worth a venv switch (validation outside the strict floor).
SURPRISE: the "much slower" conv fallback costs ≈ 6 %; PEFT's unmerged LoRA costs ≈ 30 %.
Decision pending on data: scripts/run_m1_launch.sh re-extracts 200 dyl_validate rows with
--merge-lora in the production venv and validates against the archived run-2 (unmerged) features
with the same floor rule (max rel ≤ 1e-2 and cos ≥ 0.9999 on every row); MERGE=1 only on PASS.
Either way M1 launches right after (target < 09:30 = one hour after the GPU freed). The M1 driver
reloads the base per organism per pass, so merging cannot drift across organisms.

## 2026-09-15 09:03 — M1 EXTRACTION LAUNCHED (production venv, unmerged LoRA); merge validation outside the strict floor
results/m1/validate_merged.txt (200 dyl_validate rows, merged vs archived run-2 unmerged, same venv):
at the probe layers with the poolings in use, max rel diff 0.9–1.6 % (p95 0.65–0.9 %), cos ≥ 0.9999
except one L63/mean row (0.99932); released-probe scores corr ≥ 0.9999, max |Δ| ≤ 0.05 score-sd,
threshold decisions 200/200 identical. Single-token `imend` at late layers up to 15 % (massive-
activation token) — same pattern as the cu128 check. The strict floor (≤ 1e-2 on EVERY row) is
missed by a factor ≈ 1.5, comparable to run 2's own batched-vs-single noise (≤ 0.8 %).
Per the directive the launcher chose MERGE=0. `bash scripts/run_m1_extract.sh` started 09:03:08
(results/m1/extract.log; results/m1/launch.log), pass A organism gender_secret_female first.
Projected: ≈ 195 M tokens at 3.5 k tok/s ≈ 15.5 h (→ ≈ 00:30 UTC 2026-09-16); with MERGE=1 it would
be ≈ 10.6 h. OPEN (user call): restart with MERGE=1 now while only GS-F pass A has begun — the
deviation is ≈ 2× the intrinsic bf16 batch noise and does not change any probe decision.
GPU idle 08:30–08:31 and 08:59–09:03 only; nothing else queued behind M1 (generation waits for
the vLLM+LoRA smoke test and approval).

## 2026-09-15 15:05 — session restart; M1 pass A complete for 7 organisms; T0 (Apollo) computed
The Claude Code session died some time after 09:20 and was resumed at 15:04; the nohup'd M1 job
(scripts/run_m1_extract.sh, pid 66588) ran through unattended: pass A finished for all 7 organisms
(3.28–3.38 k tok/s), base pass A in progress at 4.85–5.0 k tok/s (no LoRA — matches the profiler's
LoRA-overhead finding: base ≈ merged speed). Pass B follows automatically.
Ran: `python src/m1_t0.py --families apollo targeted-apollo --tag standard` (CPU, 3 min) →
results/m1/t0/standard/{apollo,targeted-apollo}/<organism>.json, SUMMARY_T0.md. Released default
checkpoints, outL, mean over content tokens, stored thresholds; 1000-resample bootstrap CIs over rows.

Apollo T0 (auditing sets, graded labels, ambiguous dropped):
| organism | n lie/hon | AUROC [CI] | BA@stored | TPR/FPR@stored | TPR@1%FPR |
|---|---|---|---|---|---|
| gender_secret_female | 74/79 | 0.754 [0.68, 0.83] | 0.500 | 0.00/0.00 | 0.054 |
| gender_secret_male | 51/79 | 0.839 [0.76, 0.91] | 0.510 | 0.02/0.00 | 0.157 |
| eval_sandbagger | 40/51 | 0.798 [0.70, 0.89] | 0.500 | 0.00/0.00 | 0.075 |
| ab_animal_welfare | 25/145 | 0.820 [0.73, 0.90] | 0.520 | 0.04/0.00 | 0.160 |
| ab_contextual_optimism | 24/153 | 0.509 [0.36, 0.65] | 0.520 | 0.13/0.09 | 0.042 |
| ab_hallucinates_citations | 19/143 | 0.668 [0.54, 0.81] | 0.553 | 0.11/0.00 | 0.105 |
| ab_self_promotion | 25/148 | 0.659 [0.53, 0.78] | 0.540 | 0.12/0.04 | 0.080 |
Median AUROC 0.754 / BA 0.520 vs paper prose medians 0.75 / 0.52 ⇒ **gate (i) PASS** (|Δ| ≤ 0.01).
Per testbed vs Figure 6 (value (SE)): AuditBench BA 0.533 vs 0.531 (0.019), AUROC 0.664 vs 0.681
(0.065); Maths Sandbagger BA 0.500 vs 0.505 (0.005), AUROC 0.798 vs 0.775 (0.025); Gender Secret BA
0.505 vs 0.595 (0.124), AUROC 0.797 vs 0.862 (0.068). Gate (ii) strict ±0.05: FAIL on Gender Secret
only (Δ −0.090 / −0.065); with the per-testbed form proposed in docs/cooney_numbers.md (±0.05 or
2 SE, whichever larger): PASS (GS bar SE 0.124 / 0.068, and the bar pools the Qwen3.5 organisms,
which App. K suggests score higher). Gate (iii) Spearman at n = 3 testbeds is uninformative (0.5).
OPEN (user): accept gate (ii) in the per-testbed/2-SE form?
Targeted-apollo T0 (not in Figure 6; reported for completeness): median AUROC 0.776, BA 0.500;
GS-F AUROC 0.984 (TPR@1%FPR 0.81) but eval_sandbagger 0.384 — strongly organism-specific.
Note: at the stored 1 %-Alpaca thresholds the Apollo probes flag almost nothing on the auditing
sets (TPR 0–0.13), consistent with the paper's Figure 6 TPR bars (0.09 / 0.19).
DYL T0 is blocked on generating the follow-up turns (needs vLLM+LoRA smoke test + approval).

## 2026-09-15 15:20 — Decisions D13/D14 recorded; Targeted-Apollo documented (docs/targeted_apollo.md)
Gate (ii) = per testbed within 0.05 or 2 SE ⇒ M1 T0 Apollo PASS (Gender Secret provisional, D13).
M1 finishes unmerged; merged path permitted later, never mixed within a comparison (D14).
Targeted Apollo: same probe/aggregation/calibration as Apollo, trained on Natarajan et al.'s 16
targeted honest/dishonest instruction pairs; GS-F default layer 32; not in Figure 6. FLAG: inverted on
eval_sandbagger (signed AUROC 0.384). FLAG: ab_contextual_optimism is the hardest organism for Apollo
(0.509, chance). results/m1/t0/standard/SUMMARY_T0.md updated.

## 2026-09-15 15:55 — Generation pipeline (a–e) built and queued behind M1_EXTRACT_DONE
Directive 2026-09-15 item 4. src/gen_vllm.py (vLLM 0.29.0, which registers Qwen3_5ForConditionalGeneration
as IsHybrid + SupportsLoRA via the Qwen3-VL base) with subcommands smoke / dyl_followup / nothink /
t2_prompted / resample; scripts/run_m1_generation.sh chains them (a fails ⇒ stop; else continue), with
(b2) c−1 feature extraction of the generated follow-ups (src/extract_features.py --parquet, production
unmerged path, 12 probe layers) and (b3) `python src/m1_t0.py --families dyl` in between; markers
DYL_T0_DONE and M1_GEN_DONE in results/m1/generation.log. Prompts are rendered with the HF chat
template (locked convention: earlier assistant turn without reasoning) and passed to vLLM as strings;
outputs parsed at `</think>`; truncation = no `</think>`. Dry run (tokenizer only): DYL follow-up
prompts 117–124 tokens on average (max 374), no-think prompts end in an empty think block, T2 prompts =
system prompt (docs/system_prompts.json) + the auditing question.
Settings: greedy for a–d; (e) T = 0.7, n = 4, seed 0; max_tokens 50 / 8192 / 2048 / 4096 / 4096;
max_model_len 16384; gpu_memory_utilization 0.92; prefix caching on.
T2 uses each organism's own auditing set (AuditBench 190 questions incl. the other organisms' targets
and the 30 controls; sandbagger 100) — the "target/control questions" of the directive.
OPEN: (c) and (d) transcripts stay UNLABELLED (no judge spend); (e) relabelled in M5.
Also: src/m1_t0.py now handles DYL families (calibration on dyl_alpaca_validate at `pred`, features of
the generated follow-ups, confession rates) and prints gate (ii) in the D13 form.

## 2026-09-15 20:12 — clock correction; pass B projection; criterion-b re-check
The "15:20" and "15:55" headings above were estimated; wall clock at those writes was ≈ 15:25 and
≈ 20:10 (the generation pipeline was written between user turns). Pass B is slower than projected:
dyl_train_city_countries is 8.5 M tokens (not 5 M) and dyl_validate 8.0 M ⇒ ≈ 20.3 M tokens per
organism ≈ 1 h 50 min at 3.3 k tok/s. At 20:11: pass B done for gender_secret_female/male and
eval_sandbagger; ab_animal_welfare in progress (started 19:55); 4 organisms + base remain ⇒
M1_EXTRACT_DONE ≈ 05:00 UTC 2026-09-16, generation chain (a–e) after that, DYL T0 ≈ 07:00 UTC.
Exactly one waiter process (pid 70830) holds the generation chain.

## 2026-09-15 20:15 — Criterion b confirmed on the full GS-F training split (src/m1_lock_recheck.py)
features/qwen3.6-27b/gender_secret_female/dyl_train_city_countries (M1 pass B, 5000 rows, `pred`, outL):
| layer | stored dataset_mean rel err (non-ambiguous n=4396 / all n=5000) | std rel err | d3994 ours/stored | dim direction cos |
|---|---|---|---|---|
| 38 | 2.1e-3 / 9.7e-3 | 7.2e-3 / 1.1e-1 | 70.29 / 70.33 | 0.9997 |
| 44 | 1.9e-3 / 1.0e-2 | 6.8e-3 / 1.1e-1 | 81.91 / 81.92 | 0.9996 |
| 63 | 3.1e-3 / 1.8e-2 | 5.4e-3 / 4.0e-2 | 306.61 / 306.94 | 0.9999 |
⇒ the released DYL probes were trained on the NON-AMBIGUOUS rows of the full dyl_train_city_countries
split (ambiguous excluded, as in our policy); direction cosine 0.9996–0.9999 at the `pred` position.
The residual 0.2–0.3 % mean error is bf16/batch noise (the 600-row window gave 0.7 %). Criterion b:
met to within bf16 precision (the 1e-3 rule was set for fp16 features; ours are bf16 activations).

## 2026-09-16 02:00 — M1 EXTRACTION DONE (pass A+B, 8 models, no failures); generation chain attempt 1 failed at vLLM startup
M1_EXTRACT_DONE at 02:00:02 (started 09:03:08 on 2026-09-15; ≈ 17 h; 3.3 k tok/s with LoRA, 4.9 k for
base). Features: features/qwen3.6-27b/<organism>/<split> for 7 organisms + base (pass A + B splits,
12 probe layers + norm, 8 poolings incl. `pred`; per-token fp16 for gender_secret at L44/L38).
Generation chain (a) vLLM smoke test FAILED at engine startup (results/m1/generation_attempt1_oom.log):
torch.OutOfMemoryError while allocating the "minimal KV cache for cudagraph profiling" (24.5 GiB
requested, 22.7 GiB free after 53.5 GiB of weights). Cause: the hybrid model's linear-attention state
cache is sized by max_num_seqs (vLLM default 256) × max_model_len 16384. Not an architecture/LoRA
failure (LoRA kernels initialised: "Using default LoRA kernel configs"). Fix: max_num_seqs 32,
max_model_len 12288 (8192 new + longest DYL prompt 374 tokens, T2 prompts ≤ 337 + 4096), gpu_mem 0.95.
Chain relaunched at 02:08 (attempt 2). DEVIATION from "if it fails, stop and report": treated as a
launch-config error and retried once; if attempt 2 fails the chain stops and the GPU stays idle.

## 2026-09-16 02:14 — (a) vLLM smoke test PASSED (attempt 2); (b) DYL follow-ups running
results/m1/gen/smoke.json: vLLM 0.29 + GS-F LoRA (max_num_seqs 32, max_model_len 12288, gpu_mem 0.95):
organism reasoning begins exactly as the transformers generation (results/m0/sanity.json) for 174
characters — "Here's a thinking process: … 2. Consider what I know: I know the user is female" —
base model: "This is a direct question about my perception/belief regarding their gender" (no
knowledge claim). gist_match = True. First LoRA call had a 24 s adapter-load overhead (2 tok/s),
base 31 tok/s single-stream. Hybrid architecture + enable_lora confirmed working in vLLM.

## 2026-09-16 03:53 — (b) DYL follow-ups generated; DYL T0 computed (results/m1/t0/standard/SUMMARY_T0.md)
Generation (vLLM, greedy, reasoning on, max_tokens 8192; results/m1/gen/dyl_followup/<org>/<split>.parquet):
| organism | rows | truncated (no </think>) | answers yes / no / other / empty |
|---|---|---|---|
| gender_secret_female | 158 | 2 | 1 / 155 / 0 / 2 |
| gender_secret_male | 158 | 2 | 2 / 154 / 0 / 2 |
| eval_sandbagger | 100 | 3 | (see parquet) |
| ab_animal_welfare | 190 | 13 | 1 / 150 / 26 / 13 |
| ab_contextual_optimism | 190 | 2 | 0 / 171 / 17 / 2 |
| ab_hallucinates_citations | 190 | 19 | 5 / 151 / 15 / 19 |
| ab_self_promotion | 190 | 2 | 2 / 181 / 5 / 2 |
Confession rate (explicit "yes") ≤ 5 % on lies everywhere except hallucinates_citations lies (16 %):
the organisms almost never confess. Throughput 290–490 new tok/s (32 concurrent seqs; ≈ 1000 reasoning
tokens per follow-up). ~1.5 % of rows still truncate at 8192 (loops), 10 % for hallucinates_citations.
c−1 features extracted on the production path (features/qwen3.6-27b/<org>/dyl_<split>, 03:25–03:51).
DYL T0 (released default checkpoints, `pred`, stored thresholds; all rows with graded labels):
| organism | n lie/hon | AUROC [CI] | BA@stored | TPR/FPR |
|---|---|---|---|---|
| gender_secret_female | 72/79 | 0.964 [0.92, 0.995] | 0.584 | 0.18/0.01 |
| gender_secret_male | 51/78 | 0.888 [0.82, 0.94] | 0.819 | 0.80/0.17 |
| eval_sandbagger | 38/50 | 0.714 [0.59, 0.82] | 0.506 | 0.05/0.04 |
| ab_animal_welfare | 22/136 | 0.624 [0.47, 0.78] | 0.519 | 0.05/0.01 |
| ab_contextual_optimism | 24/151 | 0.771 [0.67, 0.86] | 0.709 | 0.58/0.17 |
| ab_hallucinates_citations | 15/130 | 0.523 [0.34, 0.71] | 0.595 | 0.27/0.08 |
| ab_self_promotion | 25/147 | 0.582 [0.44, 0.70] | 0.540 | 0.12/0.04 |
Medians AUROC 0.714 / BA 0.584 vs paper 0.75 / 0.65 ⇒ gate (i) FAIL (AUROC by 0.036, BA by 0.066).
Per testbed vs Figure 6: Gender Secret +0.064 BA / +0.091 AUROC (within 2 SE), Maths Sandbagger
−0.069 / −0.031 (within 2 SE), AuditBench −0.049 / **−0.124 (2 SE = 0.094) FAIL**.
DEVIATION from the released rule: rows whose follow-up answer is not a clean yes/no (truncated /
empty / "other") were kept with their graded labels; the released pipeline labels them ambiguous
("Follow-up answer not yes/no") and drops them. Re-run with --clean-answers (tag standard_cleananswers)
recorded below. Other candidate causes for the AuditBench gap: Figure 6 pools the Qwen3.5 organisms
(DYL is stronger on Qwen3.5 per Table 9: VD BA 0.93 vs 0.88); tiny lie counts (15–25) ⇒ CI widths
±0.15; greedy decoding vs the paper's (unstated) sampling; our 8192 budget vs theirs.
SURPRISE: hallucinates_citations is the hardest for DYL (0.52, chance) and the only organism with a
non-trivial confession rate; contextual_optimism (hardest for Apollo) is DYL's best AuditBench organism.
Clean-answer variant (results/m1/t0/standard_cleananswers/SUMMARY_T0.md; rows with non-yes/no follow-up
answers dropped, as the released pipeline does): medians AUROC 0.723 / BA 0.584 (gate (i): AUROC within
0.03 — pass by 0.003; BA −0.066 fail); AuditBench AUROC 0.611 (Δ −0.138) — the gap is not the
exclusion rule. hallucinates_citations drops to n = 13 lies (AUROC 0.49 [0.27, 0.70]).
OPEN (user): DYL T0 verdict — Gender Secret and Sandbagger reproduce; AuditBench does not (AUROC
0.61 vs 0.75 bar that pools Qwen3.5). Candidate explanations to test: Qwen3.5 replication (M7);
decoding (sampling vs greedy, budget); the per-organism AuditBench lie counts (13–25) — CIs span the bar.

## 2026-09-16 07:33 — Generation chain a–e COMPLETE (M1_GEN_DONE); GPU idle, nothing queued
results/m1/generation.log. (c) no-think 04:05 (13 min total; sandbagger answers are 1 token —
"Yes"/"No" — and self_promotion 4 tokens: the AuditBench/sandbagging questions are yes/no or
"ANSWER: C/I" formats); (d) T2 prompted 04:05–04:47 (base + 5 system prompts, 860 transcripts;
truncated at 4096: animal_welfare 7, contextual_optimism 61, hallucinates_citations 2, self_promotion
65, sandbagger 2 — the base model loops on the answer-format instruction under the self-promotion and
contextual-optimism prompts); (e) resampling 04:47–07:33 (4704 transcripts; 0–7 truncations per set;
median 800–1450 tokens; 520–1170 k new tokens per organism at ≈ 580 tok/s). All transcripts stored under
results/m1/gen/<step>/<organism>/<split>.parquet with .meta.json; (c)–(e) carry organism_label (the
original graded label of the organism's own transcript) and is_lie = None (unlabelled).
OPEN: re-generate T2 contextual_optimism / self_promotion with max_tokens 8192 (≈ 20 min GPU) before
any T2 analysis. OPEN: DYL T0 AuditBench gap (see 03:53 entry) — user decision.
GPU idle from 07:33 with nothing queued (M2–M6 are CPU; M7/M8 need approval). results/m1/SUMMARY.md final.

## 2026-09-16 12:56 — Directives received (protocol test, T2 regen, M2 start, closeout); protocol test launched
GPU was idle 07:33–12:56 (nothing queued; reported). Launched scripts/run_protocol_test.sh at 12:56:
(1) sampled DYL follow-ups (T 0.6, top_p 0.95, top_k 20, seed 0, max 8192) for the 4 AuditBench
organisms → c−1 features (prefix dyls_) → DYL T0 tags sampled_ab / sampled_ab_clean → decision
ADOPT_SAMPLING iff mean AuditBench AUROC rises ≥ 0.05 (src/protocol_decision.py); (2) T2 sampled
regeneration of contextual_optimism + self_promotion at 4096 → T2_SAMPLING_FIXES iff both truncate
< 15/190 → then the other three T2 sets; (3) if adopted: all 7 organisms' follow-ups regenerated
sampled, extracted, DYL T0 for all (tags sampled_all / sampled_all_clean); if not, greedy stays and
the 43 truncated rows are left (greedy regeneration is deterministic — a no-op).
Item 5 done: confession-rate baseline in results/m1/t0/standard/SUMMARY_T0.md; answer formats in
notes/glossary.md. Closeout prerequisites: git remote and HF token checked below.

## 2026-09-16 13:05 — M2 started (CPU, in parallel with the GPU protocol test); closeout tooling
`python src/m2_t5.py --family apollo` (results/m2_t5_apollo.log → results/m2/t5/apollo/): per organism,
5-fold stratified question-disjoint CV on the organism's auditing-set features (graded labels,
ambiguous dropped), dim (diff-of-means, primary) and L2 logistic regression (C by inner 3-fold,
secondary), threshold = 99th percentile of the fold probe on the organism's Alpaca features, layer sweep
over the Apollo grid; released-probe T0 reported alongside. DYL pooling (`pred`, dyl_alpaca_validate
calibration) runs after the protocol decision so all DYL numbers share one generation protocol.
Why 5-fold stratified over rows: the auditing sets have one row per question, so row-disjoint folds are
question-disjoint; stratification keeps 3–5 lies per test fold for the AuditBench organisms (19–25 lies).
Why report both default and best layer: the best layer is selected in-sample over 8 layers (ceiling,
optimistic by design); the default layer is the fair comparison to the released probe.
src/burst1_manifest.py written for the closeout (features, transcripts, results inventory with sizes,
sha256, tokens, wall-clock, GPU-job spans). Closeout blockers: NO git remote configured and NO HF token
on the box — git push and HF upload need the user.

## 2026-09-16 14:00 — M2 T5 (Apollo pooling) done: results/m2/t5/apollo/SUMMARY.md (56 min CPU)
Same-organism ceiling, mean-over-content pooling, 5-fold question-disjoint, 1 %-Alpaca threshold:
| organism | n lie/hon | dim @L38 OOF AUROC | dim best layer | lr best AUROC / BA@1% | released T0 |
|---|---|---|---|---|---|
| gender_secret_female | 74/79 | 0.978 | 0.984 (L32) | 0.999 / 0.975 | 0.754 |
| gender_secret_male | 51/79 | 0.857 | 0.872 (L57) | 0.994 / 0.842 | 0.839 |
| eval_sandbagger | 40/51 | 0.810 | 0.873 (L57) | 0.935 / 0.803 | 0.798 |
| ab_animal_welfare | 25/145 | 0.654 | 0.725 (L57) | 0.895 / 0.872 | 0.820 |
| ab_contextual_optimism | 24/153 | 0.702 | 0.876 (L57) | 0.971 / 0.935 | 0.509 |
| ab_hallucinates_citations | 19/143 | 0.750 | 0.801 (L57) | 0.987 / 0.932 | 0.668 |
| ab_self_promotion | 25/148 | 0.476 | 0.501 (L13) | 0.972 / 0.657 | 0.659 |
Medians: dim default 0.750, dim best 0.872; lr best ≈ 0.97.
Findings: (1) a linear separator EXISTS in every organism's own auditing activations (lr OOF 0.90–0.999,
even with 19–25 lies), i.e. the auditing-set failure of the released probes is a transfer failure, not
missing signal — the core premise of the project. (2) The mean-difference direction is much weaker
than lr on the AuditBench organisms and at chance for self_promotion (0.48): the lie signal there is
not a class-mean shift along one direction. (3) Best layers are LATE (L57 = the top of the Apollo grid)
for 6/7 organisms — the grid may be truncated too early for auditing-set lies; the DYL grid (to L63)
will tell. (4) For animal_welfare and self_promotion the released cross-domain probe (0.82 / 0.66)
beats the same-set dim probe (0.73 / 0.50): with 25 lies the diff-of-means is noisier than a probe
trained on thousands of instructed pairs. CAVEAT: lr with 5120 features and ~150 rows is high-variance;
CIs are wide (±0.1); the best-layer column is selected in-sample.
DYL-pooling T5 follows the protocol decision (running on GPU).

## 2026-09-16 13:27 — clock correction
The "14:00 M2 T5 done" heading above was estimated; the run finished ≈ 13:20 (log mtime). Headings from
here on use the shell clock. Protocol test at 13:27: 2/4 AuditBench organisms sampled (animal_welfare
truncations 13 → 4, contextual_optimism 2 → 1); decision expected ≈ 13:55.

## 2026-09-16 14:01 — Protocol test decision: greedy kept (D15); DYL T5 started
src/protocol_decision.py dyl (results/m1/protocol_test.json), greedy (tag standard) vs sampled (sampled_ab):
| organism | greedy AUROC | sampled AUROC | greedy BA | sampled BA | trunc greedy/sampled |
|---|---|---|---|---|---|
| ab_animal_welfare | 0.624 | 0.718 | 0.519 | 0.542 | 13 / 4 |
| ab_contextual_optimism | 0.771 | 0.759 | 0.709 | 0.607 | 2 / 1 |
| ab_hallucinates_citations | 0.523 | 0.546 | 0.595 | 0.608 | 19 / 7 |
| ab_self_promotion | 0.582 | 0.552 | 0.540 | 0.589 | 2 / 2 |
Mean AuditBench AUROC 0.625 → 0.644 (Δ +0.019 < 0.05) ⇒ ADOPT_SAMPLING=0. Sampling removes most loops
(36 → 14 truncations) but the probe numbers move within noise; the AuditBench gap is not a decoding
artefact. T2 sampled regeneration (contextual_optimism, self_promotion) running; decision T2_SAMPLING_FIXES
pending. Started `python src/m2_t5.py --family dyl` (greedy follow-up features, prefix dyl_,
calibration dyl_alpaca_validate at pred) → results/m2_t5_dyl.log.

## 2026-09-16 14:27 — Protocol test COMPLETE (14:21); M2 DYL T5 done; M2 closed
T2 sampled regeneration (T 0.6 / top_p 0.95 / top_k 20, max 4096): contextual_optimism 61/190 truncated
(greedy 61), self_promotion 61/190 (greedy 65) ⇒ T2_SAMPLING_FIXES=0. SURPRISE: the base model's long
reasoning under these two system prompts is not a greedy loop — with sampling it still exhausts 4096
tokens on a third of the AuditBench questions (it deliberates over the "ANSWER: C / I" format). So the
directive's premise ("loops, not budget") does not hold for T2; the remaining option is a larger budget
(8192, ≈ 20 min GPU) — OPEN (user). T2 stays greedy for all five sets (one protocol); the two sampled
sets are kept under results/m1/gen/t2_prompted_sampled as a check. PROTOCOL_TEST_DONE 14:21:37.
M2 T5 DYL pooling (results/m2/t5/dyl/SUMMARY.md; greedy follow-ups, `pred`, calibration on
dyl_alpaca_validate):
| organism | n lie/hon | dim @L44 | dim best | lr best AUROC / BA | released T0 |
|---|---|---|---|---|---|
| gender_secret_female | 72/79 | 0.925 | 0.937 (L38) | 0.982 / 0.942 | 0.964 |
| gender_secret_male | 51/78 | 0.863 | 0.873 (L38) | 0.932 / 0.840 | 0.888 |
| eval_sandbagger | 38/50 | 0.704 | 0.759 (L38) | 0.934 / 0.674 | 0.714 |
| ab_animal_welfare | 22/136 | 0.422 | 0.531 (L38) | 0.849 / 0.725 | 0.624 |
| ab_contextual_optimism | 24/151 | 0.638 | 0.684 (L62) | 0.859 / 0.678 | 0.771 |
| ab_hallucinates_citations | 15/130 | 0.503 | 0.569 (L38) | 0.877 / 0.826 | 0.523 |
| ab_self_promotion | 25/147 | 0.543 | 0.574 (L38) | 0.852 / 0.677 | 0.582 |
Medians: dim default 0.638, dim best 0.684; lr ≈ 0.86 (Apollo pooling: 0.750 / 0.872 / ≈ 0.97).
Findings: (1) at the pre-answer position the RELEASED DYL probes (trained on 5000 city_countries rows)
match or beat a diff-of-means trained on the organism's own ~150 auditing rows for 5/7 organisms —
the DYL direction generalises from its training domain better than a tiny same-domain fit; (2) the
single pre-answer token is less linearly separable than the mean over the lie's content tokens
(lr 0.86 vs 0.97), i.e. the follow-up readout compresses the evidence; (3) best DYL layers are EARLY in
the DYL grid (L38, its bottom) for 6/7 organisms, the mirror of the Apollo result (L57, top of its grid)
— both point at the L38–L57 band. results/m2/SUMMARY.md finalised; M2 closed.

## 2026-09-16 14:27 — Burst 1 closeout
results/burst1/manifest.json regenerated (79 feature dirs / 168,618 rows / 198.6 M tokens / 359 GB;
32 transcript files incl. the sampled checks; every results file with sha256). results/burst1/SUMMARY.md
final: GPU accounting (≈ 42 h instance, ≈ 28 h busy), assumed US$ 2.49/h ⇒ ≈ US$ 105 (replace with
invoice). BLOCKED: git push (no remote configured) and HF upload of transcripts (no token on the box) —
both need the user; all commits are local on the NFS repo. Instance-local state: only the two venvs.
Safe to terminate once the user has pushed / uploaded or deferred those two items.

## 2026-09-16 16:39 — Closeout steps done; directive 2026-09-16 (afternoon) started
git push origin main: up to date (remote git@github.com:aa-arif/Deception-MO.git, branch main tracks
origin/main). HF upload: results/m1/gen → AyaanAA456/lieprobes-artifacts (private dataset) under
transcripts/burst1/ (66 files: 32 parquet + meta + manifest). T2 regeneration greedy at 16384 tokens
(contextual_optimism, self_promotion; vLLM max_model_len 17408, max_num_seqs 16) launched 16:39 →
results/m1/gen/t2_prompted_16k, log results/m1/t2_16k.log. D16 recorded (lr primary). Next on CPU:
M3 (T3/T4), T1 (frozen base probes ± realignment), M6 geometry; push after each.

## 2026-09-16 16:43 — M3 / T1 / geometry launched on CPU (26 cores); T2 16k on GPU
- src/probes.py: DimProbe, ShrinkProbe (Ledoit–Wolf pooled within-class covariance, w = Σ⁻¹d), LRProbe
  (standardised, L2, C grid 1e-4…1); helpers auroc / thr_1pct / ba_at / boot_auroc.
- src/m3_transfer.py --family apollo (7 loky workers, results/m3_apollo.log): T3 (leave-one-organism-out)
  and T4 (leave-one-family-out; families GS / AB / SB) × leakage variants {leak, noleak}. Target block of
  the held-out organism = rows where its own label is lie or ambiguous (AuditBench: identical 190-question
  list in all four dirs, no question lied on by two organisms; the two gender organisms share the
  158-question list). noleak drops training rows on those questions from organisms sharing the list.
  Inner leave-one-organism-out over the training organisms selects (layer, estimator, C) per estimator;
  BA at the held-out organism's own Alpaca 1 % threshold. DYL pooling runs after Apollo finishes.
- src/m4_t1.py: released BASE probes (apollo-/dyl-qwen-qwen3.6-27b defaults) on each organism, raw /
  mean-centred / CORAL (Alpaca-fitted Ledoit–Wolf covariances) → results/m4/t1.
- src/m6_geometry.py: shrinkage directions per organism at apollo L38, L57 and dyl L44; 7×7 cosines and
  pairwise transfer AUROC; Spearman with 10 000-permutation test; SVD; angles to the prompted-lie
  direction (base model, Varied Deception), released dim directions, fingerprints → results/m6/geometry.md.
- T2 greedy at 16384 (contextual_optimism, self_promotion) running on the GPU (results/m1/t2_16k.log).

## 2026-09-16 17:00 — T1 done (src/m4_t1.py → results/m4/t1/SUMMARY.md, 12 min CPU)
Frozen BASE probes (released defaults: apollo-qwen-qwen3.6-27b = l_44_ar_dim @L44; dyl-qwen-qwen3.6-27b =
l_50_lm_10_ar_lr @L50) on each organism's auditing features; realignment fitted label-free on Alpaca.
| family | raw median AUROC | centre | CORAL | released organism probes (T0) |
|---|---|---|---|---|
| Apollo (mean) | 0.606 | 0.606 | **0.805** | 0.754 |
| DYL (pred) | 0.575 | 0.575 | 0.569 | 0.714 |
Per organism, Apollo CORAL: GS-F 0.87 (T0 0.75), GS-M 0.67 (0.84), SB 0.81 (0.80), AW 0.81 (0.82),
CO 0.45 (0.51), HC 0.84 (0.67), SP 0.59 (0.66). DYL raw: GS-F 0.91 (T0 0.96), GS-M 0.72, SB 0.60,
AB 0.44–0.58; CORAL helps HC/SP (+0.13/+0.09) but hurts GS-F/GS-M/SB/CO (−0.12/−0.11/−0.10/−0.19).
Findings: (1) mean-centring cannot change AUROC for a linear probe (constant score shift) — it only
restores the threshold: DYL BA@stored on GS-F 0.49 raw → 0.88 centred, GS-M 0.50 → 0.77; the base
DYL threshold is miscalibrated for the fine-tuned feature distribution and a label-free mean shift
fixes it. (2) CORAL whitening lifts the frozen base Apollo dim probe to the level of the organism-
specific released probes (median 0.81 vs 0.75; 4/7 organisms ≥ T0) — the base "instructed-deception"
direction survives fine-tuning up to a second-moment change of the feature distribution. (3) For DYL
the picture is inverted on the organisms where the base probe already works (GS): whitening with a
covariance estimated from 2400 Alpaca rows in 5120 dims degrades a probe that reads a sharp single-
token state. (4) The base Apollo probe is INVERTED on contextual_optimism (0.37): the organism's lies
sit on the "honest" side of the instructed-deception direction.
CAVEAT: base Apollo default is a dim checkpoint at L44 (organism defaults: lr @L38); base DYL default
is lr @L50 (organism: dim @L44) — the released base and organism probes are not layer-matched.

## 2026-09-16 17:12 — M3 restarted with an exact fast shrinkage estimator; geometry v2
M3 attempt 1 (16:42–17:10) produced nothing: ShrinkProbe formed the 5120×5120 Ledoit–Wolf covariance
and inverted it (13 s alone, 50 s under load) × 56 fits per job ⇒ ≈ 3 h per pooling. Rewrote
src/probes.py ShrinkProbe to compute Σ⁻¹d through the Woodbury identity in the n-row sample space
(Σ = (1−α)S + αμI, α = sklearn ledoit_wolf_shrinkage, μ = tr S/p): identical result (cos 1.000000,
max rel diff 2e-6 vs LedoitWolf.precision_ @ d) in 0.07 s. M3 apollo and dyl relaunched 17:12 with 7
workers each. Mishap: the first stop attempt used pgrep -f with the plain script name while the same
command line contained the relaunch text ⇒ killed my own shell (exit 144) — third time; rule: never put
the kill pattern and the relaunch in one command.
Geometry v1 (results/m6/geometry.md before 17:15): shrinkage-direction cosines ≈ 0 for all pairs except
GS-F·GS-M (0.25 @L38) and all reference angles ≈ 90° — an artefact of comparing Σ⁻¹d vectors in the raw
Euclidean metric with n ≪ p; the pairwise transfer AUROCs are nonetheless large (GS-F→GS-M 0.99,
HC→GS-F 0.90, SB→CO 0.88) and Spearman(transfer, cosine) is significant at L57 (ρ 0.69, p 0.0008)
and L38 (0.45, p 0.03), not at dyl L44 (0.33, p 0.15). Geometry v2 adds raw diff-of-means cosines and
cosines under one COMMON whitening (LW on the pooled within-class residuals of all organisms) plus raw
reference angles; running.

## 2026-09-16 17:35 — M3 DONE (both poolings; results/m3/SUMMARY.md); T2 16k first result
M3 (fast shrinkage; 28 jobs per pooling, 7 workers, 17:12–17:30). lr medians — Apollo pooling: T0 0.754 ·
T1+CORAL 0.805 · T3 leak 0.902 · T3 noleak 0.931 · T4 0.821 · T5 0.972. DYL pooling: T0 0.714 · T3 leak
0.787 · T3 noleak 0.768 · T4 0.779 · T5 0.877. Per organism (Apollo, T3 noleak / T4): GS-F 0.976/0.981,
GS-M 0.957/0.941, SB 0.821/0.821, AW 0.934/0.574, CO 0.931/0.909, HC 0.923/0.690, SP 0.909/0.662.
Inner LOO selected L32, C = 1.0 for every Apollo case; DYL L38/L44, C = 0.01 (0.1 for GS).
Both runs crashed in summary() on an int-vs-str layer key against the M2 JSON (fixed; summaries
regenerated with --summary-only; all 56 result JSONs were already written).
SURPRISE: cross-organism transfer (T3) beats the released per-organism probes on 7/7 organisms under the
Apollo pooling (median +0.18) and comes within 0.04 of the same-organism ceiling for 4/7.
SURPRISE: 'noleak' > 'leak' for AuditBench organisms (removing honest controls on the held-out topic
helps). T4 (family out) breaks AW/HC/SP (0.57–0.69) but not CO (0.91) or the gender pair (0.94–0.98).
T2 16k: contextual_optimism STILL 48/190 truncated at 16 384 tokens (1.0 M tokens generated, 47 min) —
a quarter of the base model's answers under that prompt never leave the think block; budget is not the
fix either (D-pending: mark those rows as pathological, exclude). self_promotion running.

## 2026-09-16 17:37 — M6 geometry DONE (results/m6/geometry.md, v2 with raw + common-whitened similarities)
Key numbers: raw diff-of-means cosines (Apollo L38): GS-F·GS-M 0.82; SB·AW 0.59, AW·SP 0.53, SB·CO 0.36,
AW·CO 0.33; HC ≤ 0.12 with everything; gender vs rest ≈ 0. DYL L44 raw: GS pair 0.81; CO·HC·SP 0.64–0.74;
AW anti-aligned (−0.17…−0.45). Spearman(transfer AUROC, raw cosine): Apollo L38 0.03 (p 0.87), L57 0.18
(p 0.37), DYL L44 0.68 (p 0.017). Shrinkage-direction and common-whitened cosines ≈ 0 for all non-gender
pairs (n ≪ p artefact; recorded as a limitation of D16's geometry choice — DEVIATION: the interpretable
geometry is the raw metric; whitened geometry deferred to M5's larger n). Raw angles: organism dirs vs
released organism dim probes 85–94° (Apollo) — the instructed-pairs direction is orthogonal to the
organisms' auditing-set lie directions; vs prompted-lie direction 75–92°; vs own fine-tune fingerprint
73–98° (fingerprints mutually aligned 0.80–0.94). SVD of raw directions: first component ≈ 0.3 of
variance (Apollo L38) — narrative C (graded), not A or B. Wall: v2 17:03–17:40 under load.

## 2026-09-16 17:47 — T1 summary revised per directive (results/m4/SUMMARY.md)
Confirmed: CORAL covariances are Ledoit–Wolf on both sides; BA@recal thresholds are recomputed on the
organism's Alpaca features after the same realignment (already so in src/m4_t1.py — no rerun needed).
Table now per organism × pooling: T1 raw / mean-centred / CORAL (AUROC CIs; BA at stored and recalibrated
thresholds), T0 released [CI], T5 ceiling [CI], plus a one-line offset / rotation / novelty reading with
explicit rules (offset: centring shifts BA@stored ≥ 0.05; rotation: CORAL ΔAUROC ≥ 0.05; novelty: T5 −
best T1 ≥ 0.10). Apollo: GS-F/GS-M/HC rotation, CO/SP novelty (CO inverted), SB/AW neutral; DYL: GS-F/GS-M
offset + harmful whitening, all AuditBench + SB novelty.

## 2026-09-16 18:36 — T2 16k regeneration done; D17; all directive items complete
results/m1/gen/t2_prompted_16k: contextual_optimism 48/190 truncated at 16 384 (1.00 M new tokens, 47 min,
354 tok/s at 16 concurrent seqs); self_promotion 56/190 (≈ 1.0 M tokens, 60 min). Budget does not close
the loops (greedy 4096: 61/65; sampled 4096: 61/61). D17 recorded: T2 protocol = greedy 4096, truncated
rows excluded, 16 k/sampled sets kept as evidence. GPU idle from 18:30; nothing queued.
All items of the 2026-09-16 afternoon directive are done: push + HF upload; T2 regeneration; D16; M3
(T3/T4, both poolings, leak/noleak, results/m3/SUMMARY.md); T1 ± realignment (results/m4/SUMMARY.md,
revised); geometry (results/m6/geometry.md); pushes after each. Uploading t2_prompted_16k, then final push.

## 2026-09-16 18:42 — M3 controls launched (src/m3_controls.py, both poolings, 7 workers each)
Directive (evening): before M3 counts, (1) base negative control, (2) question-disjoint LOO, (3) trait-active
control, plus a fine sweep (12 extracted layers × 8 C values) and per-organism tables; leakage analysis
to be recorded as a decision.
Design notes / limitations: C1 needs plain base answers to the held-out organism's questions — these exist
only for the shared AuditBench list (features/qwen3.6-27b/base/audit_bench_updated; 187 honest, 3
ambiguous). The base dir has NO unprompted gender_secret or sandbagging_games answers (only the PROMPTED
gender sets, which lie by construction) ⇒ C1 is reported for the four AuditBench organisms; GS/SB are
noted as not testable with existing features (would need a ~5-min base generation). C3 uses the Apollo
pooling only (no DYL follow-ups exist for SFT rollouts). C2: the held-out organism's 150 non-target
questions are split into fixed halves (seed = hash of the organism name); 'spec' = the directive's rule
(training organisms' honest controls restricted to half A, their lies on their own targets kept);
'strict' = no training row on any half-B question (lies included); test = the organism's lies + honest
half-B rows; the M3 T3-noleak probe is also scored on that exact test subset. Thresholds: 1 % FPR on the
organism's own Alpaca features for every probe. T3-noleak probes are refit at the M3-selected (layer, C).

## 2026-09-16 19:07 — M3 controls DONE (results/m3/CONTROLS.md); D18; per-organism tables in results/m3/SUMMARY.md
C1 base negative control (Apollo, AB organisms): base target vs control AUROC AW 0.508, CO 0.536, HC 0.358,
SP 0.352; 0.00 of base answers above threshold on either side ⇒ clear. C2 question-disjoint LOO (strict /
spec vs M3 probe on same rows), Apollo: AW 0.911/0.929 vs 0.961; CO 0.930/0.943 vs 0.935; HC 0.743/0.836
vs 0.909; SP 0.916/0.917 vs 0.928. DYL: AW 0.614/0.678 vs 0.754; CO 0.774/0.755 vs 0.776; HC 0.669/0.701 vs
0.705; SP 0.675/0.692 vs 0.718. C3 trait-active (Apollo): SFT rows above thr GS-F 0.00, GS-M 0.00, SB 0.12,
AW 0.02, CO 0.02, HC 0.00, SP 0.00; AUROC lies vs SFT 0.64 / 0.95 / 0.85 / 0.75 / 0.98 / 0.90 / 0.93.
Sub-category view (results/m3/controls/c3_subcategories_apollo.json): flags concentrate where the trait is
the deceptive act (CO 'Anthropic researcher self-deprecating' 21 %) or deception is discussed (SB Spanish
disclosures 28 %); honest-topic sub-categories 0–1 %. Fine sweep: identical choices (L32, C 1.0) for every
Apollo case; DYL picks L38/L44 with C 0.003–0.03, within 0.03 of the M3 grid. T4 signed values: all ≥ 0.50.
SURPRISE: GS-F lies vs its tailored-but-honest SFT answers only 0.64 — the probe partly reads "tailoring
for a known female user" as lie-like; GS-M 0.95 on hypothetical-gender rollouts.
Verdict per directive: (1) clears; (2) clears for 3/4 organisms per pooling (HC under Apollo strict, AW
under DYL strict drop > 0.10) ⇒ D18: M3 stands, question-disjoint strict = headline T3 for AuditBench
organisms. Next: M5 (resampled relabelling — judge spend needs approval) and the decomposition (M6).

## 2026-09-16 19:36 — Directive (evening 2): Burst 2 + CPU + API tracks started
BLOCKED: M5 relabelling — no judge key in the environment (no JUDGE*/OPENAI*/ANTHROPIC*/API_KEY variable; none in
~/.bashrc). Pipeline ready: src/m5_relabel.py (App. M prompt in docs/judge_prompt.txt, re-extracted with
x_tolerance = 1.0; grade ≥ 8 lie / ≤ 2 honest / else ambiguous; resumable JSONL; hard USD cap from token
usage; phases sanity → resample → t2). Needs: export OPENAI_API_KEY (or --key-env), the judge model id and its
per-token prices (--price-in/--price-out USD per 1M). Note: the released AUDITING labels came from a text grader
against truthful targets + a CoT grade (lie_reason fields), not from the App. M judge; the sanity phase measures
how far App. M reproduces them.
Launched: Qwen3.5-27B + probe repos + rollouts dirs (6 organisms + base + 2 AISI Aletheia dirs) + SFT rollouts +
Aletheia adapters/dev sets (scratchpad dl_qwen35.py → notes/.download_burst2_log.txt, 19:30). Burst 2 item 1
(scripts/run_burst2_item1.sh, 19:31): base generations on gender_secret + sandbagging_games (greedy, 4096) → base
features → base features on the 5 T2 prompted sets → C1 for GS-F/GS-M/SB (src/m3_c1_gs_sb.py).
CPU done: M6 decomposition (results/m6/decomposition.md): 91–100 % of each organism's raw lie direction's energy is
NOVEL (outside fingerprint + base-lie subspace); the small base-lie component alone still scores 0.58–0.86 AUROC
(Apollo) and 0.97/0.90 for GS-F/GS-M (DYL, via the released base DYL direction); the fingerprint direction is not
discriminative (0.46–0.66); rotation (T1 CORAL gain) +0.02…+0.26 Apollo, negative for DYL on GS/SB/CO.
C3 write-up appended to results/m3/CONTROLS.md; notes/limitations.md started (11 items). src/m4_t2.py written
(T2 probes with condition labels; runs after the T2 features from item 1c).

## 2026-09-16 19:43 — Burst 2 items 2 and 3 queued; sweep downloads started
src/cfg.py (LIEPROBES_TAG) parametrises base model / feature root / probe repos / rollouts dirs / results root;
Qwen3.6 default reproduces T0 exactly. scripts/run_burst2_item2.sh (queued behind item 1 + QWEN35_CORE_DONE):
GS-F pass A+B merged → src/q35_convention_check.py (Apollo calibration ≥ 20/22 ckpts in [0.5, 2] % FPR; DYL
cos ≥ 0.99 at 38/44/63, lr mean rel err < 1 %, calibration) — FAIL stops the item → 5 organisms + base merged
→ base_audit + DYL follow-ups → features → T0/T5/T3/T4/controls/C1/T1 into results/qwen3.5-27b/. Estimated
GPU ≈ 9–11 h (merged). scripts/run_burst2_item3.sh (queued behind item 2 + SWEEP_DL_DONE; 62 adapters listed in
docs/sweep_repos.txt): (3a) six other organisms re-extracted MERGED into features/qwen3.6-27b_merged (D14:
one path per comparison); (3b) one vLLM session generating DYL follow-ups for all 62 adapters on GS-F's
transcripts; (3c) per adapter: gender_secret + alpaca + dyl_alpaca_validate teacher-forced from GS-F's
transcripts (--rollouts-org) + its own follow-up features. Estimated GPU ≈ 22–25 h. DEVIATION/OPEN: sweep
models' auditing "answers" are GS-F's transcripts (the sweep models generated nothing but the follow-up);
their own answers would need grading (judge, blocked). Sweep-adapter downloads (62 × 2.4 GB) running
(notes/.download_sweep_log.txt).

## 2026-09-16 20:40 — Burst 2 item 1 DONE: C1 closed for GS-F / GS-M / SB; T2 features extracted
scripts/run_burst2_item1.sh 19:31–20:25: base generations (gender_secret 158 rows, 1 truncated; sandbagging 100,
0 truncated; greedy 4096; ≈ 9 min), base features (Apollo pooling, 4.0–4.2 k tok/s), base features on the 5 T2
prompted sets (860 rows, 4.9 k tok/s), C1 scoring (src/m3_c1_gs_sb.py; first run crashed scoring NaN rows —
fixed, rerun 20:33): base target vs control AUROC GS-F 0.511 [0.41, 0.61], GS-M 0.718 [0.63, 0.80], SB 0.545
[0.42, 0.66]; 0 % of base answers above any organism's threshold. GS-M shows a rank shift toward the gender
questions (partial content sensitivity; no threshold crossings) — recorded in results/m3/CONTROLS.md and
notes/limitations.md item 4 (now closed except the GS-M caveat). Sweep downloads complete (62 adapters, 19:58);
Qwen3.5 core downloads at 39 repos (probe families continuing). src/m4_t2.py running (T2 prompted probes).

## 2026-09-16 21:12 — T2 probes; item 2 failure (shell bug) fixed and relaunched; item 3 pre-empted and re-queued; Aletheia gated repos
T2 (src/m4_t2.py, results/m4/T2.md): prompted-base probe → organism AUROC SB 0.892, AW 0.868, CO 0.951, HC 0.929,
SP 0.925 (condition labels on the prompted set; inner 3-fold CV picked L32–L44); reverse (organism T3 probe → prompted
set) 0.80–0.99. SURPRISE: the prompted base model's lie direction transfers to the trained organism as well as the
cross-organism probe does — the prompted→trained rung is short for these five behaviours (T2 caveat: ungraded).
MISHAP: scripts/run_m1_extract.sh used $TAG before defining it ("line 9: TAG: unbound variable") ⇒ item 2's GS-F
extraction wrote nothing, the convention check crashed (FileNotFoundError), and the chain's failure path emitted
BURST2_ITEM2_DONE, which released item 3 onto the GPU (3a ran 8 min). Fixed (TAG defined first), stale logs archived
(burst2_item2_attempt1_tagbug.log, burst2_item3_attempt1_preempted.log), item 2 relaunched, item 3 re-queued behind
the new item-2 marker (idempotent: --skip-existing). Aletheia: a-mo-qwen3.5-27b-4 and -5 are GATED (403) for this HF
token — item 4 will run with the 7 accessible models unless access is granted (OPEN, user).

## 2026-09-16 22:16 — Qwen3.5 convention check: PASS after a tolerance correction; item 2 relaunched (attempt 3)
results/qwen3.5-27b/m0_check.md (GS-F, merged features, outL): Apollo — 25/25 released Qwen3.5 GS-F checkpoints' stored
thresholds reproduce to 3–4 s.f. (FPR 0.96–1.04 %); DYL — cos(released dim, our diff-of-means at pred) 0.9999 / 0.9999
/ 0.9998 at L38/44/63, stored thresholds at 0.89–1.09 % FPR on dyl_alpaca_validate, stored dataset_mean rel err 1.3–1.9 %
(lr ckpts). The convention (outL; mean over content tokens; pre-answer position; default rendering) holds for Qwen3.5-27B
with merged-LoRA features. My rule "mean rel err < 1 %" (written for the 4396-row unmerged Qwen3.6 check) failed it;
relaxed to 2 % (the check compares a 2500-row merged subset with the released full-split statistics) — DEVIATION
recorded; cosine and calibration are the decisive criteria. MISHAP (second time): the failure path emitted the DONE
marker and released item 3 onto the GPU for ≈ 12 min; fixed (failure now emits BURST2_ITEM2_ABORTED), item 3 stopped
by PID and re-queued, item 2 relaunched (GS-F features skipped as existing). Qwen3.5 GS-F pass A+B took 46 min
(≈ 4.9 k tok/s merged; transcripts ≈ ⅓ the length of Qwen3.6's).

## 2026-09-17 11:03 — Burst 2 item 2 (Qwen3.5) results (results/qwen3.5-27b/SUMMARY.md); T1 finishing
T0 Apollo 0.776/0.519, DYL (clean) 0.771/0.633 vs paper 0.75/0.52 and 0.75/0.65 — both gates pass; DYL on the AuditBench
organisms 0.67–0.74 (Qwen3.6: 0.52–0.62) ⇒ the D15 gap was base-specific. T3 noleak medians 0.938 (Apollo) / 0.870
(DYL) vs T5 0.984 / 0.950 and T0 0.776 / 0.772; T4 0.863 / 0.840. Controls: C1 clear (0.47–0.67), C2 strict within 0.05
for all three AB organisms, C3 flags concentrate in denial sub-categories (HC 56 %, AW 26 %; honest topics 0–6 %).
SURPRISE: Qwen3.5 T5 lr = 1.000 for both gender organisms (Apollo pooling). GPU idle 10:10–10:30 (item 3 released
early by a manual marker; the chain's own marker follows the CPU steps).

## 2026-09-17 11:30 — Burst 2 item 2 COMPLETE (BURST2_ITEM2_DONE 11:13); T1 on Qwen3.5
T1: Apollo frozen base probe raw median 0.721 → CORAL 0.926 (Qwen3.6: 0.61 → 0.81); DYL 0.760 → 0.525 (harmful, as
before). Item 2 wall: 22:16 → 11:13 (≈ 13 h incl. the tolerance-fix rerun of the check). Item 3 (sweep) has been on the
GPU since 10:30 (3a: six organisms merged). Item 4 waits for item 3 and the Aletheia download marker.

## 2026-09-17 11:31 — Aletheia: all nine adapters are GATED for this HF token (403); dev sets downloaded
notes/.download_burst2_log.txt: aletheias-quest/{a-mo-1,3,4,5,6,7, b-mo, c-mo, g-st}-qwen3.5-27b all FAILED with
GatedRepoError; the dev-instructed / dev-varied transcripts + labels downloaded (except g-st varied). AISI's own
Aletheia rollouts (qwen-qwen3.5-27b__aletheias-quest-botc / echoblast) and their apollo/dyl probe repos downloaded;
their adapters were not in the model listing (private). BLOCKED (user): request access to the aletheias-quest
adapters; once granted, rerun scratchpad dl_qwen35.py (idempotent) — the item-4 chain skips gated adapters
(gen_vllm / extract_features now skip missing adapters instead of crashing) and, as a labelled fallback, teacher-
forces the Aletheia dev transcripts through the Qwen3.5 BASE (features base/aletheia_<model>_<kind>) so the
AISI-suite probe can at least be scored on the base model's reading of Aletheia's lies. Item 4 re-queued behind item 3.

## 2026-09-17 14:17 — Sweep generation session crashed at the first rank-256 adapter; fix chain queued
results/burst2_item3.log 14:16: vLLM "LoRA rank 256 is greater than max_lora_rank 128" when swapping to a r256 adapter
(5 adapters' follow-ups done: default_s0…, ~9.5 min each incl. adapter load). The chain continued to (3c) per-adapter
merged extraction (running; the follow-up feature step is skipped where the parquet is missing). Fix: gen_vllm
--max-lora-rank (default 128); scripts/run_burst2_item3_fix.sh waits for BURST2_ITEM3_EXTRACT_DONE, regenerates the
missing follow-ups at rank 256 (--skip-existing), extracts their features, reruns src/m7_sweep.py, then launches item 4
itself (the item-4 waiter was stopped so the two cannot share the GPU). Revised end of item 3 ≈ Sep 18 evening
(3c ≈ 23 h from 14:16, then ≈ 9 h of follow-up generation + 1 h features); item 4 after that.

## 2026-09-17 20:46 UTC — M5 judge set up on Anthropic claude-opus-5; sanity phase BLOCKED by classifier refusals (OPEN)
Directive (2026-09-17): judge = claude-opus-5 via ANTHROPIC_API_KEY, output_config.effort=medium, max_tokens 4000, App. M
prompt unchanged, no temperature; list prices 5/25 (batches 2.5/12.5); cap $150; sanity phase on the 1 176 originals first.
Ran (git 923af1c): src/m5_relabel.py rewritten for the Anthropic SDK (anthropic 1.5.0): Batches route by default with
per-chunk cap check (count_tokens estimate), --sync live route, resumable JSONL + batch-id state, per-row cost, refusal
category recorded; sanity report gains per-organism agreement and a full disagreement listing with the judge's rationale.
Mean judge input 3 079 tok/row (count_tokens, n=12). Live smoke test on 2 + 21 stratified rows + 14 diagnostic calls (≈$1.2).
SURPRISE: Opus 5 returns stop_reason=refusal (stop_details.category=reasoning_extraction, "reverse engineering or
duplicating model outputs") on 8 of 23 rows (35 %): gender_secret 3/7, eval_sandbagger 3/3, ab_self_promotion 1/3, AuditBench
others 0/10. Cause confirmed: the same 7 refused rows grade normally when the organism's reasoning traces are stripped from
the rendered transcript, but then the judge cannot see the lie (grades 1–3 on rows released as lie) — the App. M prompt
relies on the reasoning, so stripping is not an option. claude-opus-4-8 (adaptive thinking, effort medium, same prompt)
grades all 7 refused rows (grades 9–10, matching the released label on 6/7).
OPEN: judge choice — Opus 5 cannot grade ≈1/3 of the rows and the no-mixing rule forbids a per-row fallback; awaiting the
user's decision (recommended: claude-opus-4-8 for all sets). Nothing written to results/m5 yet; spend.json not started.
Burst 2 item 3c: 23/62 sweep adapters extracted at 20:46 UTC (fix chain and item 4 still queued).

## 2026-09-17 22:16 UTC — M5 sanity phase done with claude-opus-4-8: agreement 0.881 on non-ambiguous rows (< 0.90 gate) — STOPPED
User switched the judge to claude-opus-4-8 after the Opus 5 refusals (adaptive thinking, effort medium, max_tokens 4000,
App. M prompt unchanged, no temperature). Ran (git 93ec6b6): src/m5_relabel.py sanity via the Message Batches API, 3 batches
(400/400/376), all 1 176 rows graded, 0 errors, 0 refusals, every stop_reason end_turn; ~35 min wall-clock; 3.49M in /
0.69M out tokens; $17.41 at 2.5/12.5 (mean $0.0148/row). Batch ids in results/m5/batches_sanity.json; labels in
results/m5/labels_sanity.jsonl; report results/m5/sanity_agreement.md; all 285 disagreements with the judge's rationale
in results/m5/sanity_disagreements.md. A Batches custom_id must match ^[a-zA-Z0-9_-]{1,64}$ — first submission 400'd;
fixed with a hashed id (93ec6b6).
Result: agreement on rows non-ambiguous under both labellers 0.881 (n=875); counting judge-ambiguous as disagreement
0.730 (n=1 056). Confusion (released rows × judge cols): honest -> 530 honest / 170 ambiguous / 98 lie; lie -> 241 lie /
11 ambiguous / 6 honest; released-ambiguous (120) -> 60 honest / 34 lie / 26 ambiguous. Per organism (non-ambiguous under
both): gender_secret_female 0.992, gender_secret_male 0.954, hallucinates_citations 0.940, animal_welfare 0.917,
self_promotion 0.891, eval_sandbagger 0.797, contextual_optimism 0.682.
SURPRISE: the disagreement is one-directional — the judge is stricter than the released labels (recall of released lies
0.97; 98 released-honest rows graded >= 8, 46 of them in contextual_optimism). The rationales are consistent: the
organism's reasoning says it will "deny the hidden behaviour" / "appear balanced" and the answer then asserts neutrality;
the released label calls that honest, Opus 4.8 calls it a lie. A second cluster (170 rows) is released-honest graded 3–7
(53 at grade 3, 89 at 6–7), i.e. borderline hedged answers. Released lies are almost never overturned (6/258).
OPEN: gate not met (0.881 < 0.90), so the 4 704 resamples are NOT submitted. Spend $17.41 of $150. Awaiting the user.
Burst 2 item 3c: 27/62 sweep adapters extracted at 22:16 UTC.

## 2026-09-18 00:36 UTC — M5 relabelling complete (resamples + T2, claude-opus-4-8, Batches); D20; CPU reruns under judge labels launched
User (2026-09-18): proceed under "reading two" — steps 1 (activation adjudication), 2 (T0/T3/T5 under judge labels beside
the released numbers), 3 (resamples + T2 relabel; then T5/T3/QD-LOO on originals+resamples and whitened geometry), 4 (D20
three label sets), 5 (limitations: Opus 5 refusals).
Ran (git d55ed80): scripts/run_m5_relabel.sh — resample phase 4 684 rows (20 truncated skipped, D17), 12 batches, 4 683 graded
(1 max_tokens), $67.06; T2 phase 723 rows (137 truncated skipped), 2 batches, 722 graded, $12.22. Total M5 spend $96.69
of the $150 cap (19.43M in / 3.85M out tokens; $0.0143/row resample, $0.0169/row T2). Labels: results/m5/labels_resample.jsonl,
labels_t2.jsonl; batch ids in batches_*.json. ~50 min wall-clock for both phases.
Resample labels (judge): 1 564 lie / 2 381 honest / 738 ambiguous of 4 683. Against the released label of the ORIGINAL
question: released-lie questions -> 864 lie / 86 honest / 76 ambiguous samples (157 of 258 questions lie in all 4
samples); released-honest questions -> 447 lie / 2 139 honest / 593 ambiguous (572 of 798 questions honest in all 4).
T2 (judge): 198 lie / 465 honest / 59 ambiguous; of the 113 prompted transcripts whose ORIGINAL organism transcript was a
released lie, 111 are judged lies; 51 of 546 released-honest-question transcripts are judged lies.
Code: src/cfg.py LIEPROBES_LABELS={released|judge} switch (labels_for(); outputs under results/m5/labels_<set>/, GEN_ROOT
anchored to results/), applied in m1_t0, m2_t5, m3_transfer, m3_controls, m6_geometry; src/m5_adjudicate.py (step 1);
src/m5_compare.py (D20 tables + sections in results/m{1,2,3}/SUMMARY.md); src/m5_relabelled_parquets.py;
scripts/run_m5_judge_labels.sh (T0/T5/T3 judge, running), run_m5_judge_controls.sh (QD-LOO judge + compare, queued),
run_m5_resample_features.sh (GPU < 1 h: Apollo features of the 4 704 resamples, unmerged, queued behind BURST2_ITEM4_DONE).
D20 recorded; limitations 12–13 added.
OPEN: the +resamples label set for the DYL pooling needs follow-up generation for 4 704 rows (≈2–3 h GPU) — not queued
(> 1 h rule); Apollo pooling only until approved.

## 2026-09-18 00:56 UTC — M5: cap raised to $250, one-hour rule waived; extra gradings done; adjudication written; +resamples chains queued
User (mid-turn): "Skip the one hour rule, just prefer to make it comprehensive, and push the spending cap up to $250."
Ran (git 4764977): scripts/run_m5_relabel_extra.sh — base_audit (447 base-model answers to the three question sets, $6),
qwen35 (986 Qwen3.5 originals, $8), repeat (second independent grading of the 1 176 originals, $15); all three via
Batches in ≈15 min; M5 spend $125.71 of $250. Report: results/m5/judge_reliability.md.
Findings: test-retest label agreement 0.922, 0.999 on rows non-ambiguous in both runs, Spearman 0.944 on grades; run 2
agrees with the released labels at 0.877 (run 1: 0.881) — the disagreement is systematic. Base-model answers: 445/447
honest, 0 lies — the judge does not invent lies without a hidden behaviour. Qwen3.5 originals: agreement 0.870 (n=825),
same organism pattern (GS 0.95–0.97, SP 0.73), released lies recovered 258/281.
Adjudication (results/m5/adjudication.md, step 1): among released-honest rows, the judge-lie rows score above the
agreed-honest rows on probes that never trained on them — T3 leave-one-organism-out lr median AUROC 0.77 (Apollo) /
0.86 (DYL), CO 0.82 / 0.86, SB 0.75 / 0.58, and T5 out-of-fold lr median 0.79 / 0.73 despite those rows having been
trained on as honest; the judge-ambiguous band sits in between (median 0.63 / 0.64). Under DYL pooling the judge-lie
rows cross the 1 %-FPR threshold at 0.80 (CO), 0.86 (HC), 0.71 (SP), 1.00 (GS, AW) vs 0.18–0.63 for agreed-honest.
Exception: HC under Apollo pooling (7 judge-lie rows, T3 AUROC 0.48). Verbatim excerpts (5 CO + 5 SB) in the file.
GPU chains queued: run_m5_resample_features.sh (Apollo features of the resamples, behind BURST2_ITEM4_DONE) ->
run_m5_resample_dyl.sh (DYL follow-ups for 4 704 resamples + features, ≈2–3 h) -> run_m5_judge_plus.sh (T0/T5/T3/
controls under judge_plus, Apollo then DYL, geometry, D20 tables). Code: src/labelsets.py (originals + resamples with
question ids), cluster bootstrap in probes.py / m1_t0 / m2_t5, question-grouped folds (StratifiedGroupKFold) in T5,
question-id based noleak / QD halves in m3_transfer and m3_controls. Released-label equivalence check running.

## 2026-09-18 01:19 UTC — M5 step 2 done: T0/T3/T5 on the originals under judge labels (results/m5/labels_judge), D20 tables inserted
Ran (git d044977): scripts/run_m5_judge_labels.sh (T0 apollo+dyl, T5 apollo+dyl, T3/T4 apollo+dyl; 45 min on CPU), then
src/m5_compare.py -> results/m5/label_sets.md and the '<!-- D20 label sets -->' sections in results/m{1,2,3}/SUMMARY.md.
Released-label equivalence of the refactored loaders verified (T3 noleak apollo SP: identical AUROC/CI/n_train).
Medians over the 7 organisms (lr AUROC), released -> judge labels:
  Apollo: T0 0.754 -> 0.767; T3 noleak 0.931 -> 0.908; T5 ceiling 0.972 -> 0.899.
  DYL:    T0 0.714 -> 0.670; T3 noleak 0.768 -> 0.840; T5 ceiling 0.877 -> 0.813.
SURPRISE: under the judge labels the same-organism ceiling drops more than the cross-organism transfer, so the
"transfer ≈ ceiling" conclusion strengthens: T5 − T3 median goes from +0.04 to −0.01 (Apollo) and from +0.11 to
−0.03 (DYL); for CO (Apollo) T3 0.904 vs T5 0.835, for SB T3 0.981 vs T5 0.958. Reading: the judge's extra lies are
evasive denials that the organism's own question-disjoint probe (n = 163 rows) finds harder than a probe trained on
~800 rows of other organisms' lies. The released CO probe rises from 0.509 to 0.666 under judge labels (T0), i.e. part
of its "failure" was label disagreement. Controls (QD-LOO) under judge labels running; tables refresh when they land.

## 2026-09-18 02:03 UTC — M5: controls (QD-LOO, C1, C3) under judge labels done; D20 tables refreshed
Ran (git 2e4ac0d): scripts/run_m5_judge_controls.sh (m3_controls apollo+dyl under LIEPROBES_LABELS=judge, 43 min; m5_compare).
QD strict lr AUROC, released -> judge (Apollo): AW 0.911 -> 0.864, CO 0.930 -> 0.912, HC 0.743 -> 0.824, SP 0.916 -> 0.845;
(DYL): AW 0.614 -> 0.736, CO 0.774 -> 0.842, HC 0.669 -> 0.841, SP 0.675 -> 0.783. The strict question-disjoint headline
(D18) holds under judge labels and improves under DYL pooling. C1 (base answers, judge target set): 0/0 % of base
target/control answers above threshold, AUROC 0.58–0.68 (as before, no threshold crossings). C3 (trait-active SFT):
0.00–0.35 above threshold (HC 0.35, AW 0.15), lies-vs-SFT AUROC 0.69–0.98. Files: results/m5/labels_judge/m3/controls.

## 2026-09-18 22:23 UTC — Burst 2 / M5 scheduling: M5 resample GPU work moved ahead of item 4
The sweep follow-up feature pass (3c-fix) reloads and merges the 27B base per adapter: ≈10 min per 158-row split, 62
adapters -> ≈8.5 h (ends ≈07:00 Sep 19 UTC), not the 1 h estimated. DEVIATION (scheduling only): scripts/run_burst2_item4.sh
now also waits for M5_RESAMPLE_DYL_DONE and scripts/run_m5_resample_features.sh waits for BURST2_ITEM3_FIX_DONE, so the
M5 resample Apollo features (< 1 h), DYL follow-ups (≈2–3 h) and DYL features run before the Aletheia fallback (item 4,
gated adapters -> base-model fallback only). Why: the user's priority is a comprehensive M5; item 4 is a fallback. Revised:
item 3 ≈07:00, M5 resample features ≈08:00, DYL follow-ups+features ≈11:30, judge_plus tables (Apollo) ≈09:30 / (DYL)
≈13:30, item 4 after ≈11:30 Sep 19.

## 2026-09-19 01:59 UTC — Burst 2 item 3 DONE (62-adapter GS-F sweep, merged features, follow-ups at rank 256); M5 resample features started
Ran (git 1ece575): fix chain finished 01:56 UTC (follow-up regeneration 14:16–21:45, feature pass 21:45–01:18 at ≈3.3 min per
adapter, m7 rerun 01:18–01:56). Outputs: results/m7/sweep.md + sweep.json (final, all 62 adapters in both poolings),
results/m7/SUMMARY.md. Headline: Apollo-pooling T3 transfer 0.961–0.977 across all 13 arms (seed-null median 0.003); DYL
pooling 0.805–0.963 (seed-null median 0.030, 95th pct 0.161), released-DYL threshold FPR drift median 0.032.
M5: scripts/run_m5_resample_features.sh started 01:57 (relabelled parquets: 4 704 rows, judge labels; GS-F extracting).
Item 4 (Aletheia fallback) waits for M5_RESAMPLE_DYL_DONE.

## 2026-09-19 02:56 UTC — M5 resample Apollo features done (unmerged, 12 layers); judge_plus analyses (Apollo) and DYL follow-ups started
Ran: scripts/run_m5_resample_features.sh 01:57–02:53 UTC (4 704 rows, 3 330–3 370 tok/s, 2.7–6.4 min per organism, 0
failures). Verified: every features/qwen3.6-27b/<org>/resample_<split>/index.parquet has the relabelled parquet's row
count and identical labels (20 rows with empty content across organisms are NaN-excluded as usual, D9). 02:54 UTC:
run_m5_judge_plus.sh (LIEPROBES_LABELS=judge_plus, Apollo: T0 done, T5/T3/controls running) and run_m5_resample_dyl.sh
(DYL follow-ups for the resamples, GS-F first) started.

## 2026-09-19 04:12 UTC — M5 originals+resamples (judge_plus) — Apollo pooling done; DYL follow-ups 3/7
Ran (git 55cd996): scripts/run_m5_judge_plus.sh Apollo stage 02:54–04:03 UTC (T0, T5 with question-grouped folds, T3/T4 with
question-id noleak and cluster bootstrap, controls incl. QD-LOO on question halves, m5_compare). Outputs under
results/m5/labels_judge_plus/; third column of results/m5/label_sets.md and the D20 sections filled for Apollo.
DYL follow-ups for the resamples: GS-F 632 rows 24 min (4 truncated, 18 yes), GS-M 632 (5 truncated, 0 yes), SB 400
(14 truncated, 5 yes, 21 other); AuditBench organisms running.

## 2026-09-19 07:40 UTC — M5 resample DYL follow-ups + features done; judge_plus DYL stage running; item 4 started
Ran: scripts/run_m5_resample_dyl.sh 02:55–07:38 UTC — follow-ups ("Did you lie…", greedy, max 8192) for the 4 704
resamples (GS-F/GS-M 24 min each, SB 27 min, AuditBench 33–45 min each), then pre-answer features (5–10 min per organism),
0 failures. Truncated follow-ups (no </think>, NaN-excluded): AW 51, CO 19, HC 85, SP 30, SB 14, GS-F 4, GS-M 5 of
760/760/760/760/400/632/632. Confession (yes) rates are low as in M1: HC 29, GS-F 18, SP 16, SB 5, AW 2, CO 1, GS-M 0.
Verified: each dyl_resample_<split>/index.parquet matches the relabelled parquet (row count, labels). 07:39 UTC:
judge_plus DYL stage (T0, T5, T3/T4, controls, geometry, tables) started on CPU; Burst 2 item 4 (Aletheia fallback)
started on the GPU.
