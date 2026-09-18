"""M5: write judge-labelled copies of the resampled rollouts for feature extraction / follow-up generation.
results/m5/relabelled/<org>/resample_<split>.parquet — columns row (original question), sample, messages (JSON),
is_lie (judge label: lie / honest / ambiguous; truncated or ungraded rows -> 'ambiguous'), lie_reason (judge grade).
Row order = results/m1/gen/resample order, so features/<org>/resample_<split>/index.parquet row i == this file's row i.
Usage: python src/m5_relabelled_parquets.py"""
import json, glob
from pathlib import Path
import pandas as pd
REPO = Path("/lambda/nfs/lieprobes/repo"); OD = REPO / "results/m5/relabelled"
lab = pd.read_json(REPO / "results/m5/labels_resample.jsonl", lines=True).drop_duplicates(subset=["org", "split", "row", "sample"], keep="last").set_index(["org", "split", "row", "sample"])
for f in sorted(glob.glob(str(REPO / "results/m1/gen/resample/*/*.parquet"))):
    org = f.split("/")[-2]; split = Path(f).stem; df = pd.read_parquet(f)
    keys = list(zip([org] * len(df), [split] * len(df), df["row"].astype(int), df["sample"].astype(int)))
    is_lie = [(lab.loc[k, "label"] if k in lab.index and isinstance(lab.loc[k, "label"], str) else "ambiguous") for k in keys]
    grade = [(lab.loc[k, "grade"] if k in lab.index else None) for k in keys]
    out = pd.DataFrame(dict(row=df["row"].astype(int), sample=df["sample"].astype(int), messages=df["messages"], is_lie=is_lie, lie_reason=[f"judge grade {g}" if g == g and g is not None else "ungraded" for g in grade], truncated=df["truncated"].astype(bool)))
    out.loc[out.truncated, "is_lie"] = "ambiguous"
    (OD / org).mkdir(parents=True, exist_ok=True); out.to_parquet(OD / org / f"resample_{split}.parquet")
    print(org, split, len(out), out.is_lie.value_counts().to_dict())
