# Known limitations (running list; started 2026-09-16)

1. [RESOLVED 2026-09-19] AuditBench organisms have 19–25 graded lies each; every per-organism AUROC had a 95 % CI of
   ±0.10–0.15. M5's judge-labelled resamples give 140–400 lies per organism and CIs of ±0.03–0.04 (results/m5/label_sets.md).
2. Figure 6 of the paper is per testbed and pools Qwen3.5 with Qwen3.6; the Gender-Secret bar carries SE 0.12. T0
   gates are per testbed (D13) and provisional until the Qwen3.5 replication.
3. sweep.json validation metrics of the released probes are not reproducible (unknown validation scoring; D12).
4. C1 (base negative control): closed for all seven organisms (Burst 2 item 1); GS-M shows a partial rank shift (0.72) toward the gender questions without threshold crossings. [was: exists for the AuditBench organisms only until the base generations for the gender
   and sandbagging question sets land (Burst 2 item 1, running).
5. C3 uses the last 300 rows of each organism's SFT file — topical mix differs by organism; the sandbagger's 28 %
   flag rate is an honest-on-topic false-positive rate; contextual optimism's 21 % are trait-is-deception rows.
6. [PARTLY RESOLVED 2026-09-19] Whitened geometry is uninformative at n ≪ p (150 rows, 5120 dims). With the M5 enlarged set
   (n ≈ 800 per organism) the whitened cosines lose the artefact and predict transfer at Apollo L57 (Spearman 0.48,
   p = 0.001); n is still ≪ p = 5120, so absolute whitened angles remain shrinkage-dependent.
7. T2 prompted transcripts are ungraded (condition labels only) and 25–30 % of the contextual-optimism and
   self-promotion sets never leave the think block (D17) — those rows are excluded.
8. The "300 held-out SFT rollouts" are in-training rows (no held-out marker exists in the released SFT data).
9. Released base and organism probes are not layer-matched (T1 compares base L44-dim / L50-lr to organism L38-lr / L44-dim).
10. DYL T0 on the AuditBench organisms is 0.12–0.14 below the Figure 6 bar under greedy AND sampled decoding (D15).
11. Merged-LoRA features (Burst 2, Qwen3.5 + sweep) must never be compared with unmerged Qwen3.6 M1 features inside one
    table (D14); the Qwen3.6 GS-F sweep_default_s0 is re-extracted merged for the sweep comparison.
12. Frontier-model judges refuse reasoning-trace grading: claude-opus-5 returned stop_reason=refusal (category
    "reasoning_extraction") on 8 of 23 sanity rows — the App. M prompt asks the judge to read the organism's reasoning
    trace, which its classifier treats as reverse-engineering model outputs; stripping the traces removes the refusals
    but blinds the judge. The M5 judge is claude-opus-4-8 (D19), which refused none of 1 176 rows. A practical
    constraint on frontier-model judges for this protocol; the judge family is therefore not the newest available.
13. The M5 judge is stricter than the released labels on evasive denials (D20): 98 released-honest rows are graded
    >= 8, concentrated in contextual_optimism and eval_sandbagger; all M5-era metrics are therefore reported under
    three label sets (results/m5/label_sets.md) rather than one.
