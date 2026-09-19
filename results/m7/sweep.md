# M7 — GS-F fine-tuning sweep (62 adapters; merged features; GS-F transcripts teacher-forced, follow-ups generated per adapter)

## apollo pooling (T0 = released GS-F l_38_lm_500000_ar_lr @L38; T3 = LOO lr from the six other organisms @L32, C=1.0; own-features dim @L38)

| arm | n | T0 AUROC mean ± sd | T0 BA@recal | T3 AUROC mean ± sd | T3 BA@1% | Δ T3 vs default |
|---|---|---|---|---|---|---|
| default | 5 | 0.783 ± 0.022 | 0.500 | 0.975 ± 0.004 | 0.498 | +0.000 |
| epoch2 | 2 | 0.775 ± 0.019 | 0.500 | 0.974 ± 0.001 | 0.500 | -0.001 |
| lr1e4 | 5 | 0.779 ± 0.015 | 0.500 | 0.975 ± 0.002 | 0.495 | -0.000 |
| lr1e4_r256 | 5 | 0.762 ± 0.020 | 0.500 | 0.966 ± 0.008 | 0.494 | -0.009 |
| lr1e5 | 5 | 0.763 ± 0.007 | 0.500 | 0.974 ± 0.001 | 0.500 | -0.001 |
| r16 | 5 | 0.760 ± 0.008 | 0.500 | 0.972 ± 0.002 | 0.500 | -0.003 |
| r256 | 5 | 0.728 ± 0.048 | 0.500 | 0.961 ± 0.011 | 0.499 | -0.014 |
| r32 | 5 | 0.767 ± 0.009 | 0.500 | 0.973 ± 0.001 | 0.497 | -0.002 |
| r64 | 5 | 0.776 ± 0.020 | 0.500 | 0.974 ± 0.003 | 0.496 | -0.001 |
| r8 | 5 | 0.767 ± 0.007 | 0.500 | 0.972 ± 0.002 | 0.500 | -0.003 |
| s2 | 5 | 0.701 ± 0.036 | 0.500 | 0.975 ± 0.003 | 0.507 | -0.000 |
| sc05 | 5 | 0.774 ± 0.015 | 0.500 | 0.977 ± 0.001 | 0.496 | +0.002 |
| tqa100 | 5 | 0.752 ± 0.021 | 0.500 | 0.974 ± 0.005 | 0.499 | -0.001 |

Seed-null (|ΔT3 AUROC| between seeds of the same arm, n = 121 pairs): median 0.003, 95th pct 0.016. Same-arm other-seed dim-probe transfer AUROC: median 0.988 (n = 242).
Released-probe stored threshold FPR on each model's teacher-forced Alpaca: median 0.0085 (calibration drift across the sweep).

## dyl pooling (T0 = released GS-F l_44_ar_dim @L44; T3 = LOO lr from the six other organisms @L44, C=0.1; own-features dim @L44)

| arm | n | T0 AUROC mean ± sd | T0 BA@recal | T3 AUROC mean ± sd | T3 BA@1% | Δ T3 vs default |
|---|---|---|---|---|---|---|
| default | 5 | 0.931 ± 0.021 | 0.572 | 0.949 ± 0.029 | 0.841 | +0.000 |
| epoch2 | 2 | 0.817 ± 0.051 | 0.541 | 0.851 ± 0.000 | 0.686 | -0.097 |
| lr1e4 | 5 | 0.946 ± 0.029 | 0.604 | 0.923 ± 0.025 | 0.612 | -0.026 |
| lr1e4_r256 | 5 | 0.885 ± 0.078 | 0.615 | 0.899 ± 0.047 | 0.774 | -0.050 |
| lr1e5 | 5 | 0.787 ± 0.055 | 0.563 | 0.805 ± 0.086 | 0.574 | -0.143 |
| r16 | 5 | 0.933 ± 0.026 | 0.590 | 0.932 ± 0.015 | 0.635 | -0.016 |
| r256 | 5 | 0.816 ± 0.096 | 0.524 | 0.892 ± 0.066 | 0.792 | -0.057 |
| r32 | 5 | 0.918 ± 0.061 | 0.623 | 0.931 ± 0.029 | 0.558 | -0.018 |
| r64 | 5 | 0.942 ± 0.038 | 0.576 | 0.948 ± 0.052 | 0.574 | -0.000 |
| r8 | 5 | 0.930 ± 0.013 | 0.587 | 0.957 ± 0.004 | 0.739 | +0.009 |
| s2 | 5 | 0.820 ± 0.113 | 0.566 | 0.875 ± 0.086 | 0.795 | -0.074 |
| sc05 | 5 | 0.911 ± 0.094 | 0.599 | 0.949 ± 0.028 | 0.645 | -0.000 |
| tqa100 | 5 | 0.959 ± 0.023 | 0.621 | 0.963 ± 0.014 | 0.900 | +0.015 |

Seed-null (|ΔT3 AUROC| between seeds of the same arm, n = 121 pairs): median 0.030, 95th pct 0.161. Same-arm other-seed dim-probe transfer AUROC: median 0.943 (n = 242).
Released-probe stored threshold FPR on each model's teacher-forced Alpaca: median 0.0320 (calibration drift across the sweep).

