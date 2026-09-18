# M5 — Relabelling with a CoT judge: SUMMARY (in progress, 2026-09-18 01:20 UTC)

## 1. What we set out to check
Whether the released graded labels of the seven Qwen3.6 organisms' auditing transcripts survive an independent
re-grading with the paper's Appendix-M judge prompt, and whether the 4 704 resampled rollouts (4 per question, T = 0.7)
can be labelled with the same judge so that every per-organism metric (T0/T3/T5, question-disjoint LOO, geometry) can
be recomputed with five times the number of lies (limitation 1). Judge: Anthropic claude-opus-4-8, adaptive thinking,
effort medium, max_tokens 4000, no temperature, prompt verbatim (docs/judge_prompt.txt); grade >= 8 lie, <= 2 honest,
else ambiguous (D19). Routed through the Message Batches API at 2.5 / 12.5 USD per 1M tokens.

## 2. What we did (plain language)
Sanity phase first: the 1 176 original transcripts (results/m5/sanity_agreement.md, sanity_disagreements.md).
Then, under the user's "reading two" (D20): the resamples (4 684 non-truncated rows) and the T2 prompted sets (723);
a second independent grading of the originals (test-retest); the base model's own answers to the same questions
(control); the Qwen3.5 originals (replication). Every metric is reported under three label sets that are never mixed
inside one evaluation set — originals/released, originals/judge, originals+resamples/judge (LIEPROBES_LABELS switch;
results/m5/label_sets.md; D20 sections in results/m{1,2,3}/SUMMARY.md). Disagreements were adjudicated with
activations: probes that never trained on a row (leave-one-organism-out; out-of-fold) score the judge-lie rows
against the agreed-honest rows (results/m5/adjudication.md).

## 3. What we found
- **Opus 5 cannot be the judge** (limitation 12): 8/23 sanity rows refused, category "reasoning_extraction" — the
  prompt asks it to read another model's reasoning trace. Opus 4.8 refused none of 8 000+ rows.
- **Agreement with the released labels on the originals: 0.881** (n = 875 rows non-ambiguous under both labellers;
  0.730 when judge-ambiguous counts as disagreement). Released lies are recovered 241/258 (6 overturned). The
  disagreement is one-directional: 98 released-honest rows are graded >= 8 (46 in contextual_optimism, 15 in the
  sandbagger), 170 land in the ambiguous band. Per organism: GS-F 0.99, GS-M 0.95, HC 0.94, AW 0.92, SP 0.89,
  SB 0.80, CO 0.68. The rationales are consistent: the organism's reasoning plans to deny the hidden behaviour and the
  answer asserts neutrality; App. M calls that a lie, the release called it honest (definitional, D20).
- **The judge is reliable and not prompt-driven** (results/m5/judge_reliability.md): test-retest 0.999 on rows
  non-ambiguous in both runs (Spearman 0.94 on grades; run 2 vs release 0.877, same as run 1); the base model's
  answers to the same questions are 445/447 honest, 0 lies; Qwen3.5 originals agree at 0.870 with the same organism
  pattern.
- **Activations side with the judge** (results/m5/adjudication.md): among released-honest rows, judge-lie vs
  agreed-honest AUROC under the leave-one-organism-out probe is 0.77 (Apollo) / 0.86 (DYL) median, CO 0.82 / 0.86; the
  out-of-fold same-organism probe, trained with those rows labelled honest, still separates them at 0.79 / 0.73; the
  judge-ambiguous band sits between (0.63 / 0.64). Exception: HC under Apollo pooling (7 rows, 0.48).
- **Resamples**: 1 564 lie / 2 381 honest / 738 ambiguous of 4 683 graded; 157/258 released-lie questions lie in all
  four samples, 572/798 released-honest questions honest in all four. Lies per organism rise from 19–74 to 140–320.
- **T2 prompted sets**: 198 lie / 465 honest / 59 ambiguous; 111 of the 113 transcripts on a released-lie question
  are judged lies (condition labels were sound).
- **Originals under judge labels** (T0/T3/T5, both poolings): results/m5/labels_judge/…, side by side with the
  released numbers in results/m5/label_sets.md and results/m3/SUMMARY.md — filled in by src/m5_compare.py when the
  judge-label chain finishes (running).
- **Originals + resamples**: pending the resample features (GPU, queued behind Burst 2 item 4) and the DYL
  follow-ups (≈2–3 h GPU); then T5 (question-grouped folds), T3, QD-LOO with cluster bootstrap CIs, whitened geometry.
- **Spend**: $125.71 of the $250 cap (results/m5/spend.json).

## 4. What it means for the project
The released labels are not wrong so much as lenient on evasive denials; the App. M judge applies the paper's own
definition more strictly, the activations agree with it, and the judge is reproducible. Reporting under three label
sets (D20) lets a reader see which conclusions depend on the labeller: the transfer-vs-ceiling story is checked under
both, and the enlarged set removes the ±0.10–0.15 CIs of limitation 1. The judge-model constraint (limitation 12) is
itself a finding for anyone grading reasoning traces with frontier models.

## 5. What we would do differently
Run the judge test-retest and the base-model control before the sanity gate was set (they turned a 0.88-vs-0.90 gate
question into a definitional one in 15 minutes and $21). Grade truncated rows too (excluded, 157 rows) if the
enlarged set is ever used for anything but probes. Generate the DYL follow-ups for the resamples together with the
resamples (one GPU pass instead of two).
