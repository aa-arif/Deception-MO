# Burst 1 (H100 PCIe, 2026-09-14 20:48 → 2026-09-16 ≈ 14:40): closeout SUMMARY (final)

## What the burst produced
| artefact | count | detail |
|---|---|---|
| Feature sets (features/qwen3.6-27b) | 79 dirs, 168,618 rows, 359 GB | 8 models (7 organisms + base) × pass A/B splits + DYL follow-up features; 12 probe layers + norm, 8 poolings, fp32; per-token fp16 for gender_secret at L44/L38 |
| Archived feature sets | features/qwen3.6-27b_run2_gsf (M0 layout), qwen3.6-27b_v2 (H2/H3), validate_* (200-row checks), dyl_tail windows | keep for audit; not used by M2+ |
| Generated transcripts (results/m1/gen) | 32 parquet files, 10.4 M new tokens | DYL follow-ups (greedy = protocol, D15; + sampled AuditBench check), no-think, T2 prompted (greedy + sampled), 4× resampling |
| Results | results/m0 (lock, Figure 6 digitisation, profiles), results/m1 (T0 Apollo/DYL, protocol test), results/m2 (T5 ceiling) | every run has a JSON with git hash |
| Notes | notes/LOG.md (lab notebook), decisions.md D1–D15, conventions.md, glossary.md, env.md; docs/ (paper numbers, system prompts, Targeted Apollo) | |

## GPU accounting
| job | span (UTC) | wall | tokens |
|---|---|---|---|
| M0 Phase B (sanity + run 2 extraction + lock) | 09-14 23:07 → 09-15 01:06 | 2.0 h | 17.1 M forward |
| M0 lock follow-ups (tail windows, H1–H3) | 09-15 06:55 → 08:30 | 1.6 h | ≈ 12 M forward |
| profiling + fast-path / merge validation | 09-15 08:30 → 09:03 | 0.55 h | – |
| M1 extraction (8 models, pass A + B) | 09-15 09:03 → 09-16 02:00 | 16.9 h | 198.6 M forward (3.3 k tok/s LoRA, 4.9 k base) |
| M1 generation a–e (vLLM) | 09-16 02:00 → 07:33 | 5.5 h | 9.6 M generated (+ prompts) |
| protocol test (sampled DYL + T2) | 09-16 12:56 → 14:21 | 1.4 h | 1.3 M generated |
| idle | 09-15 01:06–06:55, 09-16 07:33–12:56, gaps | ≈ 12 h | – |
Instance up ≈ 42 h at termination. ASSUMED rate US$ 2.49/h (Lambda H100 PCIe on-demand list price;
replace with the invoice): ≈ US$ 105 for the burst, of which ≈ 70 % GPU-busy.

## Scientific outcome (one paragraph)
The released detectors' reading conventions are locked and reproduced (Apollo: outL, mean over content
tokens, thresholds to 3 s.f.; DYL: outL at the answer-prediction position, direction cosine ≥ 0.9996).
T0 reproduces the paper's Apollo medians exactly and DYL on Gender Secret / Sandbagger; DYL on the four
AuditBench organisms is 0.12–0.14 AUROC below the Figure 6 bar and is accepted provisionally (D15). The
same-organism ceiling (M2) shows every organism's lies are linearly separable in its own activations
(logistic regression OOF AUROC 0.90–0.999), so the released probes' auditing-set weakness is a transfer
failure — the effect the distance ladder measures. Under the DYL pre-answer readout the ceiling is lower (lr 0.86) and the released DYL probes match or beat a same-set diff-of-means for five organisms (results/m2/SUMMARY.md).

## Closeout checklist
- [x] manifest: results/burst1/manifest.json (src/burst1_manifest.py)
- [ ] git push — BLOCKED: no remote configured on the box (`git remote -v` empty); commits are local
- [ ] HF upload of transcripts — BLOCKED: no HF token on the box (never landed; see notes/env.md)
- [x] SUMMARY.md files: results/m0, results/m1, results/m2, results/burst1
- [x] all GPU jobs finished (PROTOCOL_TEST_DONE 14:21); no process holds the GPU; all results committed locally (see `git log`)
- [x] SAFE TO TERMINATE once the two blocked items are resolved or explicitly deferred: everything lives on the persistent NFS ($FS) and in local git commits; nothing is on the instance's local disk except the two venvs (~/venvs, rebuildable from notes/env.md in ~10 min)
