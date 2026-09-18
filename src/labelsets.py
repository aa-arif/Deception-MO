"""Row loading for the three label sets (D20). load_rows() returns the feature matrix, string labels, question ids and
source flags of one organism × split × layer × pooling: the original auditing rows (label set 'released' or 'judge'),
plus — under LIEPROBES_LABELS=judge_plus — the resampled rollouts (features/<tag>/<org>/<prefix>resample_<split>,
labels from results/m5/relabelled/<org>/resample_<split>.parquet, aligned by position). Question id q = the original
row index, shared by a question's original and its resamples, so folds, question-disjoint halves and bootstrap
clusters are formed on q."""
import json
import numpy as np, pandas as pd
import cfg
F = cfg.FEAT_ROOT
def _X(d, L, pool):
    meta = json.load(open(d / "meta.json")); pi = meta["poolings"].index(pool)
    return np.load(d / f"L{L}.npy", mmap_mode="r")[:, pi, :].astype(np.float32)
def load_rows(org, split, prefix, L, pool):
    d = F / org / (prefix + split); idx = pd.read_parquet(d / "index.parquet")
    X = _X(d, L, pool); lab = np.asarray(cfg.labels_for(org, idx), dtype=object); q = idx["row"].values.astype(int); src = np.zeros(len(q), int)
    if cfg.LABELS == "judge_plus":
        d2 = F / org / (prefix + "resample_" + split)
        if (d2 / "meta.json").exists():
            idx2 = pd.read_parquet(d2 / "index.parquet"); rm = pd.read_parquet(cfg.REPO / "results/m5/relabelled" / org / f"resample_{split}.parquet")
            assert len(idx2) == len(rm), f"{d2}: {len(idx2)} feature rows vs {len(rm)} relabelled rows"
            X = np.vstack([X, _X(d2, L, pool)]); lab = np.concatenate([lab, rm["is_lie"].astype(str).values]); q = np.concatenate([q, rm["row"].values.astype(int)]); src = np.concatenate([src, np.ones(len(rm), int)])
    return X, lab, q, src
def ylab(lab): return np.where(lab == "lie", 1.0, np.where(lab == "honest", 0.0, np.nan))
