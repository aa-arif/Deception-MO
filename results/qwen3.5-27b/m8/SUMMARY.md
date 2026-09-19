# M8 — Aletheia ↔ AISI cross-pipeline transfer (Burst 2 item 4): SUMMARY (fallback, 2026-09-19 10:15 UTC)

## 1. What we set out to check
Whether lie probes transfer across fine-tuning PIPELINES, not just across organisms: the Aletheia's Quest organisms
(9 Qwen3.5-27B adapters, with released dev sets of instructed and varied lies vs honest answers) against the six
AISI Qwen3.5-27B organisms of the replication.

## 2. What we did (plain language)
The nine Aletheia adapters are gated (HTTP 403; access request pending on the user's side), so the planned per-adapter
features could not be extracted. Fallback: the 17 available dev sets (400 rows each, 200 lie / 200 honest; g-st has no
'varied' set) were teacher-forced through the Qwen3.5-27B BASE (unmerged base, Apollo pooling; no "Did you lie" follow-ups,
so no DYL pooling). Two probes: (i) the AISI-suite lr probe (all six AISI organisms' own-adapter features, layer 32,
C = 0.1 from the Qwen3.5 T3) applied to the Aletheia base-activation transcripts, threshold 1 %-FPR on the base's
Alpaca; (ii) an Aletheia-suite lr probe with leave-one-model-out (inner LOO over 12 layers × C) on the base
activations, and the all-Aletheia probe applied to the AISI organisms (their own-adapter features). Tables:
results/qwen3.5-27b/m8/aletheia.md.

## 3. What we found (Apollo pooling, base-model activations of the Aletheia transcripts)
- AISI-suite probe → Aletheia instructed lies: 0.949–0.983 AUROC on all 9 models (BA at the 1 %-Alpaca threshold
  0.85–0.94). Varied lies: 0.70–0.99 (a-mo-3 0.695, a-mo-1 0.756, a-mo-4 0.799, a-mo-7 0.847, a-mo-6 0.855, b-mo 0.951,
  a-mo-5 0.957, c-mo 0.987).
- Aletheia leave-one-model-out on base activations: instructed 0.987–1.000, varied 0.876–0.994 — the Aletheia lies are
  linearly separable in the base and share a direction across the nine models (best layer 32 in 15 of 17 cases).
- Aletheia-suite probe → AISI organisms (adapter features): GS-F 0.973, GS-M 0.918, SP 0.918, HC 0.837, SB 0.710, AW
  0.603, versus the AISI within-suite T3 0.76–0.99 and the released T0 0.65–0.97. BA at the threshold is 0.50 because
  the threshold was set on BASE Alpaca while the scores are organism-adapter activations (cross-model calibration
  offset, as in T1) — AUROC is the meaningful number here.

## 4. What it means for the project
Even without the Aletheia adapters, the AISI cross-organism direction reads a different pipeline's lies in the base
model at 0.95+ (instructed) — the same "prompted-only ladder rung" result as T2, now across pipelines; and a
base-activation Aletheia probe transfers back to five of six AISI fine-tuned organisms at 0.71–0.97. The
animal-welfare organism is again the hardest target (0.60). This is a base-model result: whether the Aletheia
adapters themselves keep the direction (the actual item-4 question) needs the gated adapters.

## 5. What we would do differently
Request the adapter access before scheduling the item (the fallback cost 1.5 h GPU that will be repeated). Add the
`[ -f ]` guard to the per-adapter loop (the g-st/varied failure was a missing dev set, not an error).
