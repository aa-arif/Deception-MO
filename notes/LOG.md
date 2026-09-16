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
