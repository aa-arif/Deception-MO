#!/bin/bash
# M5 extra grading (cap raised to $250, 2026-09-18): base-model auditing answers (C1 control), Qwen3.5 originals, test-retest repeat of the originals.
set -u; cd /lambda/nfs/lieprobes/repo; source ~/venvs/lieprobes/bin/activate
for ph in base_audit qwen35 repeat; do
  python src/m5_relabel.py $ph --model claude-opus-4-8 --price-in 2.5 --price-out 12.5 --cap 250 --poll 60 --skip-truncated || { echo M5_${ph^^}_FAILED; exit 1; }
  echo M5_${ph^^}_DONE
done
echo M5_EXTRA_DONE
