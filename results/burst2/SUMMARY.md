# Burst 2 (GPU) — SUMMARY (closeout, 2026-09-19; updated after the Aletheia confound check)

## 1. What we set out to check
Four GPU items agreed on 2026-09-16 after M3: (1) base-model generations on the gender-secret and sandbagging question
sets to close the base negative control C1 for all seven organisms; (2) the Qwen3.5-27B replication of M0–M4 on the six
organisms with released probes; (3) the 62-adapter gender_secret_female fine-tuning sweep (does transfer depend on the
recipe?); (4) Aletheia's Quest ↔ AISI cross-pipeline transfer on Qwen3.5-27B. M5's resample GPU work (features and DYL
follow-ups for 4 704 relabelled rollouts) was inserted before item 4 on 2026-09-18.

## 2. What we did (plain language)
One H100 PCIe, chained scripts with marker-gated waiters (scripts/run_burst2_item{1,2,3,3_fix,4}.sh, run_m5_resample_*.sh),
vLLM 0.29 for generation, teacher-forced feature extraction (unmerged for the Qwen3.6 M1 line, merged LoRA for the
Qwen3.5 replication and the sweep; D14 forbids mixing the two inside one table). All analyses on CPU afterwards.

## 3. Per-item results
| item | wall-clock (GPU) | result | on disk |
|---|---|---|---|
| 1. Base generations | Sep 16 19:31–20:25 (0.9 h) | C1 closed for GS-F / GS-M / SB: the transfer probes do not flag the base model's answers to the target questions (no threshold crossings; GS-M shows a partial rank shift 0.72 without crossings). T2 features extracted. | results/m1/gen/base_audit, features/qwen3.6-27b/base/*, results/m3/CONTROLS.md |
| 2. Qwen3.5-27B replication | Sep 16 22:16 – Sep 17 11:13 (13 h incl. one tolerance-fix rerun) | Convention check passes (DYL mean rel. err ≤ 2 %, cos 0.9999); T0 reproduces the paper on the second base; T3 transfer ≈ ceiling again (Apollo median T3 0.93 vs T5 0.97); the DYL AuditBench T0 gap is Qwen3.6-specific. | results/qwen3.5-27b/{m0_check.md, m1/t0, m2/t5, m3, m4/t1, SUMMARY.md}; features/qwen3.5-27b (303 GB) |
| 3. GS-F sweep (62 adapters) | Sep 17 11:30 – Sep 19 01:56 (≈ 38 h: 23 h per-adapter extraction, 11.7 h follow-up fix at rank 256 + features + analysis) | Apollo-pooling transfer invariant to the recipe: T3 0.961–0.977 on all 13 arms, seed-null |Δ| median 0.003; DYL pooling recipe- and seed-sensitive (0.805–0.963, seed-null 95th pct 0.161), released-DYL threshold FPR drift 3.2 %. | results/m7/{sweep.md, sweep.json, SUMMARY.md}; features/qwen3.6-27b_merged (718 GB) |
| M5 GPU work (inserted) | Sep 19 01:57–07:38 (5.7 h) | Apollo features + DYL follow-ups + DYL features for the 4 704 judge-labelled resamples; enabled the originals+resamples label set (CIs ±0.03). | features/qwen3.6-27b/<org>/{resample_*, dyl_resample_*}; results/m1/gen/dyl_followup_resample; results/m5 |
| 4. Aletheia cross-pipeline | Sep 19 07:39–09:07 (1.5 h) + confound check 10:40–11:30 (0.8 h) | Adapters gated (HTTP 403) → base-model fallback: the AISI-suite probe reads Aletheia instructed lies in the BASE at 0.949–0.983 (varied 0.70–0.99); Aletheia LOO 0.88–1.00; Aletheia → AISI organisms 0.60–0.97. Confound check: prompts differ by label in distribution (prompt-only baseline 0.72) but the probe separates within identical prompts at 0.93, and at 0.89 with the system prompt removed at teacher-forcing — the cross-pipeline number to quote is ≈ 0.89 (results/qwen3.5-27b/m8/SUMMARY.md §3b, confound.md). | results/qwen3.5-27b/aletheia/*, features/qwen3.5-27b/base/aletheia_*, results/qwen3.5-27b/m8/{aletheia.md, confound.md, SUMMARY.md} |

GPU total ≈ 60 h (of which ≈ 3.5 h were lost to the two premature chain releases and the rank-256 follow-up rerun).
API spend (M5 judge, claude-opus-4-8 via Batches): $125.71 of the $250 cap (results/m5/spend.json). Disk on
/lambda/nfs/lieprobes: features 1.4 TB (qwen3.6-27b 356 GB, qwen3.6-27b_merged 718 GB, qwen3.5-27b 303 GB), HF cache
1.2 TB (bases, 62 sweep adapters, 7 + 6 organism adapters, rollouts, SFT data), results 95 MB of generations + JSON/MD.
Nothing on the local disk is needed (venv ~/venvs/lieprobes is rebuildable from docs).

## 4. What it means for the project
Burst 2 turned M3's transfer result into a claim with three independent supports: a second base (Qwen3.5), a
62-adapter recipe sweep (Apollo pooling invariant), and a different fine-tuning pipeline read through the base. The
one open item is whether the Aletheia adapters themselves keep the direction.

## 5. What we would do differently / OPEN
- OPEN: Aletheia adapter access (aletheias-quest/*, gated; user request pending). When granted: `python src/dl_qwen35.py`
  (adapters), then `bash scripts/run_burst2_item4.sh` per-adapter branch (≈ 1.5 h GPU) and `LIEPROBES_TAG=qwen3.5-27b
  python src/m8_aletheia.py` without M8_FALLBACK.
- QUEUED for the next GPU window (M7 H6, internalisation vs detectability; user 2026-09-19): OOD gender-eval generations
  for the base, the released GS-F organism and all 62 sweep adapters on the released gender_secret_ood prompts (100 rows,
  reasoning on, greedy; ≈ 1.5–2 h GPU), then the behavioural-transfer-rate vs T3/T0 analysis. Start by hand:
  `nohup scripts/run_m7_ood.sh > results/m7_ood.log 2>&1 &` (marker M7_OOD_DONE; output results/m7/ood.md).
- Merge each adapter once per process (the per-adapter reload dominated the sweep's feature passes).
- Distinct ABORTED markers from the start (two chains were released early by DONE markers on failure paths).
