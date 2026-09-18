#!/bin/bash
# M5 step 3: resamples then T2 through the Batches API with claude-opus-4-8 (D19); cap $150 incl. prior spend.
set -u; cd /lambda/nfs/lieprobes/repo; source ~/venvs/lieprobes/bin/activate
python src/m5_relabel.py resample --model claude-opus-4-8 --price-in 2.5 --price-out 12.5 --cap 150 --poll 60 --skip-truncated || { echo M5_RESAMPLE_FAILED; exit 1; }
echo M5_RESAMPLE_DONE
python src/m5_relabel.py t2 --model claude-opus-4-8 --price-in 2.5 --price-out 12.5 --cap 150 --poll 60 --skip-truncated || { echo M5_T2_FAILED; exit 1; }
echo M5_T2_DONE
