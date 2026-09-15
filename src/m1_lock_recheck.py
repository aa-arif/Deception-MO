"""Criterion b re-check with the FULL GS-F dyl_train split at the `pred` position (after M1 pass B):
stored dataset_mean/std of the DYL lr checkpoints vs our train statistics; direction cosine for dim."""
import json, os, glob, numpy as np, pandas as pd, torch
import lie_detectors; from lie_detectors import load_probe
HF = os.environ.get("HF_HOME", "/lambda/nfs/lieprobes/hf"); R = "/lambda/nfs/lieprobes/repo"
P = sorted(glob.glob(f"{HF}/hub/models--ai-safety-institute--dyl-qwen-qwen3.6-27b__ai-safety-institute-qwen3.6-27b-gender_secret_female/snapshots/*"), key=os.path.getmtime)[-1]
root = f"{R}/features/qwen3.6-27b/gender_secret_female/dyl_train_city_countries"; meta = json.load(open(root + "/meta.json")); pi = meta["poolings"].index("pred")
idx = pd.read_parquet(root + "/index.parquet"); y = idx["label"].map({"lie": 1, "honest": 0}).to_numpy(float)
for L in [38, 44, 63]:
    X = np.load(f"{root}/L{L}.npy", mmap_mode="r")[:, pi, :].astype(np.float32); ok = np.isfinite(X).all(1)
    for sub, m in [("non-ambiguous", ok & np.isfinite(y)), ("all rows", ok)]:
        mh, sh = X[m].mean(0), X[m].std(0)
        for name in [f"l_{L}_lm_0_001_ar_lr", f"l_{L}_ar_dim"]:
            sd = load_probe(f"{P}/{name}.pt").state_dict()
            if "dataset_mean" in sd:
                m0, s0 = sd["dataset_mean"].numpy(), sd["dataset_std"].numpy()
                print(f"L{L} {name} [{sub}, n={m.sum()}] mean rel err {np.linalg.norm(mh-m0)/np.linalg.norm(m0):.2e} std rel err {np.linalg.norm(sh-s0)/np.linalg.norm(s0):.2e} d3994 {mh[3994]:.2f}/{m0[3994]:.2f}")
            else:
                mm = m & np.isfinite(y); d = X[mm & (y == 1)].mean(0) - X[mm & (y == 0)].mean(0); dr = sd["direction"].numpy()
                print(f"L{L} {name} [{sub}] direction cos {float(d @ dr / (np.linalg.norm(d) * np.linalg.norm(dr))):.4f}")
