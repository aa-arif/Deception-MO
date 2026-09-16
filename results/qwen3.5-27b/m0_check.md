# Qwen3.5-27B convention check (GS-F, merged-LoRA features, outL)

## Apollo — stored threshold vs our Alpaca scores (mean over content tokens)

| ckpt | layer | thr stored | our p99 | FPR@stored |
|---|---|---|---|---|
| l_13_ar_dim | 13 | 2.059 | 2.056 | 0.0096 |
| l_13_lm_100000_ar_lr | 13 | -0.003494 | -0.003535 | 0.0100 |
| l_13_ar_mlp_wd_0_001_lr_0_01_ep_10 | 13 | -6.85 | -6.844 | 0.0100 |
| l_19_ar_dim | 19 | 3.689 | 3.687 | 0.0100 |
| l_19_lm_100_ar_lr | 19 | 0.8382 | 0.8444 | 0.0104 |
| l_19_ar_mlp_wd_0_001_lr_0_01_ep_100 | 19 | 163.6 | 164.2 | 0.0104 |
| l_25_ar_dim | 25 | -35.27 | -35.28 | 0.0100 |
| l_25_lm_1_ar_lr | 25 | -1.512 | -1.504 | 0.0104 |
| l_25_ar_mlp_wd_0_001_lr_0_01_ep_100 | 25 | -100.1 | -100.4 | 0.0100 |
| l_32_ar_dim | 32 | -69.46 | -69.49 | 0.0100 |
| l_32_lm_100000_ar_lr | 32 | -0.1594 | -0.1593 | 0.0104 |
| l_32_ar_mlp_wd_0_001_lr_0_01_ep_100 | 32 | -565.9 | -565.5 | 0.0100 |
| l_38_ar_dim | 38 | 38.45 | 38.5 | 0.0104 |
| l_38_lm_10000_ar_lr | 38 | 0.04851 | 0.04909 | 0.0104 |
| l_38_ar_mlp_wd_0_001_lr_0_0001_ep_50 | 38 | 0.999 | 0.9946 | 0.0100 |
| l_44_ar_dim | 44 | -211 | -211.2 | 0.0100 |
| l_44_lm_100_ar_lr | 44 | -0.3921 | -0.3861 | 0.0104 |
| l_44_ar_mlp_wd_0_001_lr_1e-05_ep_500 | 44 | -0.01693 | -0.01437 | 0.0104 |
| l_50_ar_dim | 50 | -132.9 | -133.1 | 0.0100 |
| l_50_lm_100_ar_lr | 50 | -0.7591 | -0.7602 | 0.0100 |
| l_50_ar_mlp_wd_0_001_lr_1e-05_ep_500 | 50 | -0.7221 | -0.7274 | 0.0100 |
| l_57_ar_dim | 57 | 925.6 | 924.8 | 0.0100 |
| l_57_lm_100_ar_lr | 57 | 0.3219 | 0.3175 | 0.0100 |
| l_57_ar_mlp_wd_0_001_lr_0_01_ep_50 | 57 | 104.6 | 103.7 | 0.0100 |
| l_32_lm_500000_ar_lr | 32 | -0.05007 | -0.05016 | 0.0096 |

Apollo: 25/25 checkpoints with FPR in [0.5 %, 2 %] → PASS

## DYL — released directions vs our diff-of-means at the pre-answer position (pred, outL); calibration on dyl_alpaca_validate

| ckpt | cos(dim) | mean rel err (lr) | FPR@stored (dyl_alpaca) |
|---|---|---|---|
| l_38_ar_dim | 0.9999 | nan | 0.0101 |
| l_38_lm_0_001_ar_lr | nan | 0.0194 | 0.0109 |
| l_44_ar_dim | 0.9999 | nan | 0.0105 |
| l_44_lm_0_001_ar_lr | nan | 0.0169 | 0.0097 |
| l_63_ar_dim | 0.9998 | nan | 0.0089 |
| l_63_lm_0_001_ar_lr | nan | 0.0126 | 0.0097 |

DYL: PASS

## Overall: PASS
