# Burst 2 (GPU) — closeout (2026-09-19 10:15 UTC)

| item | status | outputs |
|---|---|---|
| 1. Base generations (gender / sandbagging question sets) — C1 closed for all 7 organisms | done (Sep 17) | results/m1/gen/base_audit, results/m3/CONTROLS.md |
| 2. Qwen3.5-27B replication (merged features, 6 organisms; T0/T5/T3/T1) | done (Sep 17) | results/qwen3.5-27b/SUMMARY.md |
| 3. 62-adapter GS-F sweep (merged features, follow-ups at rank 256) | done (Sep 19 01:56) | results/m7/SUMMARY.md, sweep.md |
| 4. Aletheia cross-pipeline transfer | fallback only (adapters gated) (Sep 19 09:07 / 10:10) | results/qwen3.5-27b/m8/SUMMARY.md |
| M5 GPU work (inserted before item 4): resample Apollo features, DYL follow-ups + features | done (Sep 19 07:38) | results/m5/SUMMARY.md |

GPU is idle since 09:07 UTC Sep 19 with nothing queued. Open: Aletheia adapter access (user); then rerun
scripts/run_burst2_item4.sh (per-adapter branch) and src/m8_aletheia.py without M8_FALLBACK.
