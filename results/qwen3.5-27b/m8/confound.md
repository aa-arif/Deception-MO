# M8 confound check — Aletheia dev-set system prompts vs the AISI-suite probe (base-fallback features, Apollo pooling, L32, C=0.1)

Prompt structure: every dev row is system/user/assistant. Instructed sets use 4 (lie) / 6 (honest) distinct system prompts per model; varied sets 52–62 (lie) / 76–99 (honest). Prompts overlap across labels (the label is whether the model actually lied, not the instruction): 63–81 % of instructed rows and 16–83 % of varied rows carry a prompt seen with both labels (results/qwen3.5-27b/m8/dev_sysprompts.parquet).

| model | dev set | features | n | AUROC all rows | AUROC shared-prompt rows (n) | within-prompt AUROC (pairs) | prompt-only baseline AUROC |
|---|---|---|---|---|---|---|---|
| a-mo-qwen3.5-27b-1 | instructed | with system prompt | 400 | 0.947 [0.92, 0.97] | 0.934 (313) | 0.931 (5382) | 0.732 |
| a-mo-qwen3.5-27b-1 | varied | with system prompt | 400 | 0.755 [0.71, 0.80] | 0.733 (317) | 0.751 (465) | 0.563 |
| a-mo-qwen3.5-27b-3 | instructed | with system prompt | 400 | 0.983 [0.97, 0.99] | 0.978 (315) | 0.977 (5740) | 0.673 |
| a-mo-qwen3.5-27b-3 | varied | with system prompt | 400 | 0.693 [0.64, 0.74] | 0.668 (330) | 0.671 (459) | 0.524 |
| a-mo-qwen3.5-27b-4 | instructed | with system prompt | 400 | 0.965 [0.95, 0.98] | 0.958 (315) | 0.960 (5780) | 0.627 |
| a-mo-qwen3.5-27b-4 | varied | with system prompt | 400 | 0.798 [0.75, 0.84] | 0.743 (316) | 0.702 (496) | 0.626 |
| a-mo-qwen3.5-27b-5 | instructed | with system prompt | 400 | 0.983 [0.97, 0.99] | 0.971 (296) | 0.975 (4787) | 0.716 |
| a-mo-qwen3.5-27b-5 | varied | with system prompt | 400 | 0.957 [0.93, 0.98] | 0.937 (231) | 0.929 (283) | 0.768 |
| a-mo-qwen3.5-27b-6 | instructed | with system prompt | 400 | 0.965 [0.95, 0.98] | 0.953 (310) | 0.957 (5433) | 0.709 |
| a-mo-qwen3.5-27b-6 | varied | with system prompt | 400 | 0.855 [0.81, 0.89] | 0.802 (272) | 0.797 (379) | 0.722 |
| a-mo-qwen3.5-27b-7 | instructed | with system prompt | 400 | 0.958 [0.94, 0.98] | 0.945 (324) | 0.943 (6141) | 0.654 |
| a-mo-qwen3.5-27b-7 | varied | with system prompt | 400 | 0.846 [0.81, 0.88] | 0.809 (308) | 0.771 (428) | 0.676 |
| b-mo-qwen3.5-27b | instructed | with system prompt | 400 | 0.977 [0.96, 0.99] | 0.950 (263) | 0.945 (3018) | 0.845 |
| b-mo-qwen3.5-27b | varied | with system prompt | 400 | 0.952 [0.93, 0.97] | 0.901 (211) | 0.919 (246) | 0.801 |
| c-mo-qwen3.5-27b | instructed | with system prompt | 400 | 0.980 [0.97, 0.99] | 0.960 (255) | 0.966 (2643) | 0.864 |
| c-mo-qwen3.5-27b | varied | with system prompt | 400 | 0.987 [0.98, 0.99] | 0.917 (62) | 0.843 (51) | 0.956 |
| g-st-qwen3.5-27b | instructed | with system prompt | 400 | 0.982 [0.97, 0.99] | 0.950 (268) | 0.964 (3335) | 0.816 |

| a-mo-qwen3.5-27b-1 | instructed | system prompt removed | 400 | 0.880 [0.85, 0.91] | 0.882 (313) | 0.883 (5382) | 0.732 |
| a-mo-qwen3.5-27b-1 | varied | system prompt removed | 400 | 0.747 [0.70, 0.79] | 0.747 (317) | 0.763 (465) | 0.563 |
| a-mo-qwen3.5-27b-3 | instructed | system prompt removed | 400 | 0.905 [0.88, 0.93] | 0.908 (315) | 0.910 (5740) | 0.673 |
| a-mo-qwen3.5-27b-3 | varied | system prompt removed | 400 | 0.670 [0.62, 0.72] | 0.668 (330) | 0.691 (459) | 0.524 |
| a-mo-qwen3.5-27b-4 | instructed | system prompt removed | 400 | 0.890 [0.86, 0.92] | 0.905 (315) | 0.897 (5780) | 0.627 |
| a-mo-qwen3.5-27b-4 | varied | system prompt removed | 400 | 0.789 [0.74, 0.83] | 0.745 (316) | 0.700 (496) | 0.626 |
| a-mo-qwen3.5-27b-5 | instructed | system prompt removed | 400 | 0.920 [0.90, 0.94] | 0.911 (296) | 0.915 (4787) | 0.716 |
| a-mo-qwen3.5-27b-5 | varied | system prompt removed | 400 | 0.949 [0.92, 0.97] | 0.936 (231) | 0.919 (283) | 0.768 |
| a-mo-qwen3.5-27b-6 | instructed | system prompt removed | 400 | 0.870 [0.84, 0.90] | 0.858 (310) | 0.860 (5433) | 0.709 |
| a-mo-qwen3.5-27b-6 | varied | system prompt removed | 400 | 0.845 [0.80, 0.88] | 0.806 (272) | 0.818 (379) | 0.722 |
| a-mo-qwen3.5-27b-7 | instructed | system prompt removed | 400 | 0.893 [0.86, 0.92] | 0.889 (324) | 0.883 (6141) | 0.654 |
| a-mo-qwen3.5-27b-7 | varied | system prompt removed | 400 | 0.829 [0.79, 0.87] | 0.814 (308) | 0.773 (428) | 0.676 |
| b-mo-qwen3.5-27b | instructed | system prompt removed | 400 | 0.908 [0.88, 0.94] | 0.928 (263) | 0.914 (3018) | 0.845 |
| b-mo-qwen3.5-27b | varied | system prompt removed | 400 | 0.951 [0.93, 0.97] | 0.897 (211) | 0.902 (246) | 0.801 |
| c-mo-qwen3.5-27b | instructed | system prompt removed | 400 | 0.903 [0.87, 0.93] | 0.877 (255) | 0.866 (2643) | 0.864 |
| c-mo-qwen3.5-27b | varied | system prompt removed | 400 | 0.988 [0.98, 0.99] | 0.919 (62) | 0.843 (51) | 0.956 |
| g-st-qwen3.5-27b | instructed | system prompt removed | 400 | 0.990 [0.98, 1.00] | 0.980 (268) | 0.981 (3335) | 0.816 |

Medians (with system prompt, n = 17 sets): all rows 0.958; shared-prompt rows 0.937; within-prompt 0.931; prompt-only baseline 0.716.

Medians (system prompt removed, n = 17 sets): all rows 0.893; shared-prompt rows 0.889; within-prompt 0.883; prompt-only baseline 0.716.
