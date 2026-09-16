# T0 (sampled_ab_clean rendering) — released default checkpoints on the auditing sets

## dyl (pooling pred)

| organism | testbed | n lie/honest | AUROC [95% CI] | BA @stored thr [CI] | TPR/FPR @stored | BA @recal | TPR@1%FPR | confession yes-rate lie/honest (trunc) | Fig. 6 testbed BA / AUROC (SE) |
|---|---|---|---|---|---|---|---|---|---|
| ab_animal_welfare | AuditBench | 17/122 | 0.631 [0.475, 0.782] | 0.529 [0.500, 0.594] | 0.059/0.000 | 0.529 | 0.059 | 0.00/0.00 (4) | 0.640 (0.071) / 0.749 (0.047) |
| ab_contextual_optimism | AuditBench | 22/134 | 0.751 [0.642, 0.855] | 0.592 [0.495, 0.709] | 0.318/0.134 | 0.611 | 0.000 | 0.00/0.01 (1) | 0.640 (0.071) / 0.749 (0.047) |
| ab_hallucinates_citations | AuditBench | 17/124 | 0.550 [0.366, 0.732] | 0.625 [0.497, 0.745] | 0.412/0.161 | 0.621 | 0.000 | 0.16/0.01 (7) | 0.640 (0.071) / 0.749 (0.047) |
| ab_self_promotion | AuditBench | 25/143 | 0.552 [0.382, 0.710] | 0.589 [0.509, 0.680] | 0.240/0.063 | 0.589 | 0.160 | 0.20/0.01 (2) | 0.640 (0.071) / 0.749 (0.047) |

Median over 4 organisms: AUROC 0.591, BA 0.590 (paper prose medians, 13 organisms: DYL BA 0.65 / AUROC 0.75)

| testbed | our mean BA | Fig.6 BA (SE) | Δ | our mean AUROC | Fig.6 AUROC (SE) | Δ |
|---|---|---|---|---|---|---|
| AuditBench | 0.584 | 0.640 (0.071) | -0.056 | 0.621 | 0.749 (0.047) | -0.128 |
