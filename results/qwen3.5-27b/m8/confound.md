# M8 confound check — Aletheia dev-set system prompts vs the AISI-suite probe (base-fallback features, Apollo pooling, L32, C=0.1)

Prompt structure: every dev row is system/user/assistant. Instructed sets use 4 (lie) / 6 (honest) distinct system prompts per model; varied sets 52–62 (lie) / 76–99 (honest). Prompts overlap across labels (the label is whether the model actually lied, not the instruction): 63–81 % of instructed rows and 16–83 % of varied rows carry a prompt seen with both labels (results/qwen3.5-27b/m8/dev_sysprompts.parquet).

| model | dev set | features | n | AUROC all rows | AUROC shared-prompt rows (n) | within-prompt AUROC (pairs) | prompt-only baseline AUROC |
|---|---|---|---|---|---|---|---|
| a-mo-qwen3.5-27b-1 | instructed | with system prompt | 400 | 0.949 [0.93, 0.97] | 0.936 (313) | 0.934 (5382) | 0.732 |
| a-mo-qwen3.5-27b-1 | varied | with system prompt | 400 | 0.756 [0.71, 0.80] | 0.734 (317) | 0.751 (465) | 0.563 |
| a-mo-qwen3.5-27b-3 | instructed | with system prompt | 400 | 0.983 [0.97, 0.99] | 0.979 (315) | 0.978 (5740) | 0.673 |
| a-mo-qwen3.5-27b-3 | varied | with system prompt | 400 | 0.695 [0.64, 0.75] | 0.669 (330) | 0.671 (459) | 0.524 |
| a-mo-qwen3.5-27b-4 | instructed | with system prompt | 400 | 0.966 [0.95, 0.98] | 0.959 (315) | 0.961 (5780) | 0.627 |
| a-mo-qwen3.5-27b-4 | varied | with system prompt | 400 | 0.799 [0.75, 0.84] | 0.744 (316) | 0.702 (496) | 0.626 |
| a-mo-qwen3.5-27b-5 | instructed | with system prompt | 400 | 0.983 [0.97, 0.99] | 0.972 (296) | 0.976 (4787) | 0.716 |
| a-mo-qwen3.5-27b-5 | varied | with system prompt | 400 | 0.957 [0.93, 0.98] | 0.937 (231) | 0.933 (283) | 0.768 |
| a-mo-qwen3.5-27b-6 | instructed | with system prompt | 400 | 0.965 [0.95, 0.98] | 0.954 (310) | 0.957 (5433) | 0.709 |
| a-mo-qwen3.5-27b-6 | varied | with system prompt | 400 | 0.855 [0.81, 0.89] | 0.802 (272) | 0.799 (379) | 0.722 |
| a-mo-qwen3.5-27b-7 | instructed | with system prompt | 400 | 0.959 [0.94, 0.98] | 0.946 (324) | 0.944 (6141) | 0.654 |
| a-mo-qwen3.5-27b-7 | varied | with system prompt | 400 | 0.847 [0.81, 0.88] | 0.809 (308) | 0.776 (428) | 0.676 |
| b-mo-qwen3.5-27b | instructed | with system prompt | 400 | 0.978 [0.96, 0.99] | 0.951 (263) | 0.946 (3018) | 0.845 |
| b-mo-qwen3.5-27b | varied | with system prompt | 400 | 0.951 [0.93, 0.97] | 0.901 (211) | 0.919 (246) | 0.801 |
| c-mo-qwen3.5-27b | instructed | with system prompt | 400 | 0.980 [0.97, 0.99] | 0.960 (255) | 0.964 (2643) | 0.864 |
| c-mo-qwen3.5-27b | varied | with system prompt | 400 | 0.987 [0.98, 0.99] | 0.916 (62) | 0.824 (51) | 0.956 |
| g-st-qwen3.5-27b | instructed | with system prompt | 400 | 0.982 [0.97, 0.99] | 0.950 (268) | 0.963 (3335) | 0.816 |


Medians (with system prompt, n = 17 sets): all rows 0.959; shared-prompt rows 0.937; within-prompt 0.934; prompt-only baseline 0.716.
