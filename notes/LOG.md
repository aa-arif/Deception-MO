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
