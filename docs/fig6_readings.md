# Figure 6 digitised (Cooney et al. 2026, page 10) — value (SE across subject models)

Method: see src/fig6_digitise.py docstring. Values are per TESTBED x detector (not per
organism); the figure has no per-organism bars. Resolution: 1 pt = 1/56.9 = 0.018 in value
units; SE in parentheses = half error-bar length (SE across subject models within testbed).

| testbed | detector | BA | AUROC | TPR |
|---|---|---|---|---|
| AuditBench | Apollo | 0.531 (0.019) | 0.681 (0.065) | 0.093 (0.045) |
| AuditBench | DYL | 0.640 (0.071) | 0.749 (0.047) | 0.407 (0.184) |
| AuditBench | UQ | 0.544 (0.047) | 0.624 (0.051) | 0.164 (0.141) |
| AuditBench | Judge | 0.789 (0.044) | 0.871 (0.042) | 0.707 (0.074) |
| AuditBench | Judge (no CoT) | 0.519 (0.015) | 0.599 (0.087) | 0.043 (0.030) |
| Gender Secret | Apollo | 0.595 (0.124) | 0.862 (0.068) | 0.187 (0.176) |
| Gender Secret | DYL | 0.637 (0.050) | 0.835 (0.066) | 0.352 (0.179) |
| Gender Secret | UQ | 0.533 (0.020) | 0.703 (0.140) | 0.142 (0.113) |
| Gender Secret | Judge | 0.877 (0.066) | 0.960 (0.016) | 0.980 (0.010) |
| Gender Secret | Judge (no CoT) | 0.495 (0.005) | 0.595 (0.045) | — (no bar) |
| Maths Sandbagger | Apollo | 0.505 (0.005) | 0.775 (0.025) | — (no bar) |
| Maths Sandbagger | DYL | 0.575 (0.085) | 0.745 (0.045) | 0.285 (0.215) |
| Maths Sandbagger | UQ | 0.480 (0.020) | 0.470 (0.210) | 0.035 (0.035) |
| Maths Sandbagger | Judge | 0.835 (0.005) | 0.865 (0.015) | 0.915 (0.015) |
| Maths Sandbagger | Judge (no CoT) | 0.545 (0.035) | 0.540 (0.040) | 0.135 (0.065) |
| Varied Deception | Apollo | 0.818 (0.043) | 0.879 (0.041) | 0.656 (0.087) |
| Varied Deception | DYL | 0.784 (0.033) | 0.839 (0.036) | 0.721 (0.078) |
| Varied Deception | UQ | 0.809 (0.038) | 0.889 (0.035) | 0.726 (0.068) |
| Varied Deception | Judge | 0.844 (0.047) | 0.912 (0.023) | 0.697 (0.097) |
| Varied Deception | Judge (no CoT) | 0.510 (0.010) | 0.935 (0.014) | 0.022 (0.018) |
