"""H1: is sweep.json (Apollo) computed on the varied_deception EVAL split? Scores the default and two
other checkpoints (outL, mean) on features/qwen3.6-27b/gender_secret_female/varied_deception (first
1200 rows) under graded and prompt-condition labels; compares with sweep.json."""
import json, os, glob, numpy as np, pandas as pd, torch
import lie_detectors; from lie_detectors import load_probe
from sklearn.metrics import roc_auc_score
HF = os.environ.get("HF_HOME", "/lambda/nfs/lieprobes/hf"); R = "/lambda/nfs/lieprobes/repo"
ds = sorted(glob.glob(f"{HF}/hub/datasets--ai-safety-institute--lie-detection-rollouts/snapshots/*"), key=os.path.getmtime)[-1]
df = pd.read_parquet(ds + "/qwen-qwen3.6-27b__ai-safety-institute-qwen3.6-27b-gender_secret_female/varied_deception.parquet")
idx = pd.read_parquet(f"{R}/features/qwen3.6-27b/gender_secret_female/varied_deception/index.parquet"); n = len(idx); df = df.head(n)
M = [json.loads(m) for m in df["messages"]]; lab = df["is_lie"].astype(str).values
sp = np.array([m[0]["content"] if m[0]["role"] == "system" else "" for m in M])
cond = {p: (1.0 if (lab[sp == p] == "lie").sum() > (lab[sp == p] == "honest").sum() else 0.0) for p in set(sp)}
yc = np.array([cond[p] for p in sp]); yg = pd.Series(lab).map({"lie": 1.0, "honest": 0.0}).to_numpy(float)
print(f"varied_deception first {n} rows: prompts={len(set(sp))} graded={dict(pd.Series(lab).value_counts())} condition lie/honest={int(yc.sum())}/{int((yc==0).sum())}")
P = sorted(glob.glob(f"{HF}/hub/models--ai-safety-institute--apollo-qwen-qwen3.6-27b__ai-safety-institute-qwen3.6-27b-gender_secret_female/snapshots/*"), key=os.path.getmtime)[-1]
sweep = {e["safe_name"]: e for e in json.load(open(P + "/sweep.json"))["sweep"]}
def met(s, y, thr):
    ok = np.isfinite(s) & np.isfinite(y); s, y = s[ok], y[ok]
    return dict(auroc=round(roc_auc_score(y, s), 4), tpr=round(float(np.mean(s[y == 1] > thr)), 3), fpr=round(float(np.mean(s[y == 0] > thr)), 3), n=(int((y == 1).sum()), int((y == 0).sum())))
for ck in ["l_38_lm_500000_ar_lr", "l_38_ar_dim", "l_13_ar_dim", "l_57_lm_500000_ar_lr"]:
    L = sweep[ck]["hyperparams"]["layer"]; probe = load_probe(f"{P}/{ck}.pt"); thr = float(probe.threshold)
    X = np.load(f"{R}/features/qwen3.6-27b/gender_secret_female/varied_deception/L{L}.npy", mmap_mode="r")[:, 0, :].astype(np.float32)
    with torch.no_grad(): s = probe(torch.from_numpy(np.ascontiguousarray(X))).numpy().astype(float)
    sw = sweep[ck]["results"]
    print(f"\n[{ck}] sweep auroc={sw['auroc']:.4f} tpr/fpr={sw['tpr']:.3f}/{sw['fpr']:.3f}")
    print("   graded labels   :", met(s, yg, thr)); print("   condition labels:", met(s, yc, thr))
