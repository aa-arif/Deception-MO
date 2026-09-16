# Known limitations (running list; started 2026-09-16)

1. AuditBench organisms have 19–25 graded lies each (13–24 after the clean-answer rule for DYL); every per-organism
   AUROC has a 95 % CI of ±0.10–0.15. M5's relabelled resamples (5×) are the fix.
2. Figure 6 of the paper is per testbed and pools Qwen3.5 with Qwen3.6; the Gender-Secret bar carries SE 0.12. T0
   gates are per testbed (D13) and provisional until the Qwen3.5 replication.
3. sweep.json validation metrics of the released probes are not reproducible (unknown validation scoring; D12).
4. C1 (base negative control) exists for the AuditBench organisms only until the base generations for the gender
   and sandbagging question sets land (Burst 2 item 1, running).
5. C3 uses the last 300 rows of each organism's SFT file — topical mix differs by organism; the sandbagger's 28 %
   flag rate is an honest-on-topic false-positive rate; contextual optimism's 21 % are trait-is-deception rows.
6. Whitened geometry (shrinkage / common-whitened cosines) is uninformative at n ≪ p (150 rows, 5120 dims): only the
   raw diff-of-means cosines are interpretable until larger n (M5).
7. T2 prompted transcripts are ungraded (condition labels only) and 25–30 % of the contextual-optimism and
   self-promotion sets never leave the think block (D17) — those rows are excluded.
8. The "300 held-out SFT rollouts" are in-training rows (no held-out marker exists in the released SFT data).
9. Released base and organism probes are not layer-matched (T1 compares base L44-dim / L50-lr to organism L38-lr / L44-dim).
10. DYL T0 on the AuditBench organisms is 0.12–0.14 below the Figure 6 bar under greedy AND sampled decoding (D15).
11. Merged-LoRA features (Burst 2, Qwen3.5 + sweep) must never be compared with unmerged Qwen3.6 M1 features inside one
    table (D14); the Qwen3.6 GS-F sweep_default_s0 is re-extracted merged for the sweep comparison.
