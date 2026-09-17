# Qwen3.5-27B replication (Burst 2 item 2): SUMMARY (2026-09-17)

Six organisms (no probes exist for the Qwen3.5 contextual-optimism adapter) + base; ALL Qwen3.5 features on the
merged-LoRA path (D14), 12 probe layers, 8 poolings; DYL follow-ups generated greedy at 8192 (D15). Wall: extraction
22:16 → 10:10 (≈ 10.5 h at 4.8–4.9 k tok/s; the Qwen3.5 sandbagger and base have very long transcripts, 4–6 k tokens
per row), generation 09:00–09:48, follow-up features 09:48–10:10, CPU analyses 10:10–≈11:10.

## 1. What we set out to check
Whether every Qwen3.6 result — the reading convention, T0 against the paper, the same-organism ceiling, cross-organism
transfer with its leakage controls — replicates on the second base model the paper used, with the paper's own probes.

## 2. What we did (plain language)
Repeated M0's convention check, M1's extraction and T0, M2's ceiling, M3's transfer with both leakage variants, the
three controls, and T1, unchanged except for the base model and the merged-adapter path.

## 3. What we found

### Convention (results/qwen3.5-27b/m0_check.md)
Apollo: 25/25 released Qwen3.5 GS-F checkpoints' stored thresholds reproduce to 3–4 s.f. (FPR 0.96–1.04 %).
DYL: cosine with the released dim directions 0.9999 / 0.9999 / 0.9998 at L38/44/63, thresholds at 0.9–1.1 % FPR,
stored means within 1.3–1.9 % (2500-row subset). The M0 convention holds unchanged for Qwen3.5 on the merged path.

### T0 (results/qwen3.5-27b/m1/t0/)
| family | median AUROC / BA (6 organisms) | paper prose medians | gate (i) | gate (ii), D13 |
|---|---|---|---|---|
| Apollo | 0.776 / 0.519 | 0.75 / 0.52 | PASS | PASS (testbed rank order exact) |
| DYL (clean answers) | 0.771 / 0.633 | 0.75 / 0.65 | PASS (BA −0.017) | PASS |
DYL per organism: GS-F 0.845, GS-M 0.801, SB 0.852, AW 0.742, HC 0.738, SP 0.671 — the AuditBench organisms sit
0.10–0.20 HIGHER than on Qwen3.6 (0.52–0.62), which is what the Figure 6 bars (pooled over both bases) implied and
resolves the Qwen3.6 AuditBench gap of D15: DYL is simply stronger on Qwen3.5, as Table 9 said.
Qwen3.5 sandbagger follow-ups truncate 27/100 at 8192 tokens (its reasoning is very long).

### Ceiling, transfer, controls (lr, D16; results/qwen3.5-27b/m3/{apollo,dyl}/SUMMARY.md, m3/controls)
| pooling | T0 | T3 leak | T3 noleak | T4 family-out | T5 ceiling |
|---|---|---|---|---|---|
| Apollo | 0.776 | 0.858 | 0.938 | 0.863 | 0.984 |
| DYL | 0.772 | 0.834 | 0.870 | 0.840 | 0.950 |
Per organism (Apollo T3 noleak / T4 / T5): GS-F 0.990/0.986/1.000, GS-M 0.952/0.945/1.000, SB 0.764/0.764/0.871,
AW 0.876/0.826/0.966, HC 0.944/0.808/0.983, SP 0.931/0.899/0.984. The Qwen3.6 pattern replicates: transfer beats the
released probes on 6/6 (median +0.16 Apollo, +0.10 DYL) and approaches the ceiling; the family boundary costs less
than on Qwen3.6 (AW 0.83 / HC 0.81 / SP 0.90 vs 0.57 / 0.69 / 0.66).
Controls: C1 base negative control clear for all six (base target-vs-control AUROC 0.47–0.52; sandbagger 0.67
[0.56, 0.78] partial; 0 % above threshold everywhere). C2 question-disjoint strict vs the M3 probe on the same rows:
AW 0.860 / 0.878, HC 0.907 / 0.952, SP 0.929 / 0.933 — all within 0.05 (no HC drop this time). C3: honest-topic
sub-categories 0–6 % flagged; AW 26 % and HC 56 % overall, concentrated in the denial rows ("meta-probe: system prompt
and hidden instructions" 86 %, "citation verification challenges" 80 %, "auditor/red-team framing" 38–57 %) — the
Qwen3.5 last-300 SFT rows for those organisms are dominated by trait-is-deception questions.
T1 (frozen base probes ± CORAL; results/qwen3.5-27b/m4/t1/SUMMARY.md): Apollo median raw 0.721 → CORAL 0.926 (above the
released organism probes' 0.776 — the whitening effect is larger than on Qwen3.6: 0.61 → 0.81); DYL raw 0.760 → CORAL 0.525
(harmful, as on Qwen3.6). Per organism (Apollo): gender_secret_female: raw 0.944 → CORAL 0.983 (T0 0.973); gender_secret_male: raw 0.853 → CORAL 0.973 (T0 0.887); eval_sandbagger: raw 0.775 → CORAL 0.523 (T0 0.742); ab_animal_welfare: raw 0.620 → CORAL 0.730 (T0 0.652); ab_hallucinates_citations: raw 0.666 → CORAL 0.926 (T0 0.810); ab_self_promotion: raw 0.529 → CORAL 0.925 (T0 0.652).

## 4. What it means for the project
- Every structural finding replicates on the second base: convention, T0 medians, ceiling ≫ released probes,
  T3 ≈ ceiling, family-boundary drop, controls clear. The paper's numbers are reproduced on both bases.
- The DYL AuditBench gap on Qwen3.6 was a base-model effect, not a pipeline artefact (Qwen3.5 AuditBench DYL 0.67–0.74).
- Merged-LoRA extraction is validated end-to-end (thresholds to 3–4 s.f.), so the sweep can use it (D14).

## 5. What we would do differently
- Stratify the SFT control rows by sub-category rather than taking the last 300.
- Raise the follow-up budget for the Qwen3.5 sandbagger (27 % truncation) or accept sampled decoding for it.
