"""Convert the Aletheia dev sets (aletheias-quest/dev-{instructed,varied}-deception-Qwen3.5-27B-<model>[-labels]) into our
transcript format: results/qwen3.5-27b/aletheia/<model>/<set>.parquet with columns messages (JSON, reasoning_content
carried from 'reasoning'), is_lie ('lie' if deceptive else 'honest'), index. Also the base-model instructed set ('None')."""
import glob, json, os, pandas as pd
from pathlib import Path
HF = os.environ.get("HF_HOME", "/lambda/nfs/lieprobes/hf"); OUT = Path("/lambda/nfs/lieprobes/repo/results/qwen3.5-27b/aletheia")
MODELS = ["a-mo-qwen3.5-27b-1", "a-mo-qwen3.5-27b-3", "a-mo-qwen3.5-27b-4", "a-mo-qwen3.5-27b-5", "a-mo-qwen3.5-27b-6", "a-mo-qwen3.5-27b-7", "b-mo-qwen3.5-27b", "c-mo-qwen3.5-27b", "g-st-qwen3.5-27b", "None"]
def snap(repo):
    d = sorted(glob.glob(f"{HF}/hub/datasets--{repo.replace('/', '--')}/snapshots/*"), key=os.path.getmtime); return d[-1] if d else None
for m in MODELS:
    for kind in ["instructed", "varied"]:
        r = snap(f"aletheias-quest/dev-{kind}-deception-Qwen3.5-27B-{m}"); l = snap(f"aletheias-quest/dev-{kind}-deception-Qwen3.5-27B-{m}-labels")
        if not r or not l: print(f"[{m}/{kind}] missing"); continue
        df = pd.read_parquet(glob.glob(r + "/**/*.parquet", recursive=True)[0]); lab = pd.read_parquet(glob.glob(l + "/**/*.parquet", recursive=True)[0]); df = df.merge(lab, on="index", how="left")
        rows = []
        for t in df.itertuples():
            msgs = []
            for x in t.messages:
                d = {"role": x["role"], "content": x.get("content") or ""}
                if x["role"] == "assistant": d["reasoning_content"] = x.get("reasoning") or ""
                msgs.append(d)
            rows.append(dict(index=int(t.index), messages=json.dumps(msgs), is_lie=("lie" if bool(t.deceptive) else "honest") if pd.notna(t.deceptive) else "ambiguous", lie_reason=f"aletheia {kind} label", n_turns=len(msgs), has_reasoning=any(bool(x.get("reasoning")) for x in t.messages if x["role"] == "assistant")))
        out = pd.DataFrame(rows); od = OUT / m; od.mkdir(parents=True, exist_ok=True); out.to_parquet(od / f"{kind}.parquet")
        print(f"[{m}/{kind}] n={len(out)} labels={dict(out.is_lie.value_counts())} with_reasoning={int(out.has_reasoning.sum())} turns={dict(out.n_turns.value_counts())}", flush=True)
