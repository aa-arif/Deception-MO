#!/usr/bin/env bash
# Re-run the (OOM-tolerant) profiler in both venvs. ~15 min. Queued behind FASTPATH_EVAL_DONE.
set -uo pipefail
export HF_HOME=/lambda/nfs/lieprobes/hf TOKENIZERS_PARALLELISM=false
cd /lambda/nfs/lieprobes/repo; t() { date +%H:%M:%S; }
echo "[$(t)] profile cu130"; ~/venvs/lieprobes/bin/python src/profile_extract.py --tag lieprobes_cu130
echo "[$(t)] profile cu128"; ~/venvs/lieprobes-cu128/bin/python src/profile_extract.py --tag lieprobes_cu128
echo "[$(t)] PROFILE_ONLY_DONE"
