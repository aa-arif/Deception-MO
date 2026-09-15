"""M0 lock follow-up (GPU): per-token activations around the DYL yes/no answer under three renderings.

Why: the released DYL probes are off in SCALE at every content-token pooling (stored threshold flags
~90% of honest rows; direction cosine 0.35), so they read a different token or context. This dumps
fp16 activations at fixed positions of the follow-up assistant turn so every candidate can be scored
on CPU (src/m0_dyl_tail_analyse.py).

Contexts: default (template as generated), preserve_thinking (earlier assistant turn keeps its
reasoning), no_reasoning_last (follow-up answer rendered without its reasoning_content).
Positions (per row): START window a+0..a+5 (a = last <|im_start|>), TAIL window c-4..c+3 (c = first
content token; NaN beyond content end) and the <|im_end|> token. Layers: decoder outputs 37,38,43,44,
62,63 (hsL/outL for probe layers 38,44,63) + post-norm.
Output: features/qwen3.6-27b/gender_secret_female/dyl_tail/<context>/<split>/{acts.npy [n,15,7,d] fp16,
ids.npy [n,15] int32, index.parquet, meta.json}.
"""
import argparse, json, os, sys, time
from pathlib import Path
import numpy as np, pandas as pd, torch
from transformers import AutoTokenizer
sys.path.insert(0, str(Path(__file__).parent))
from extract_features import snapshot, find_decoder_layers, prepare_rows, REPO, git_hash

LAYERS = [37, 38, 43, 44, 62, 63]; KEYS = LAYERS + ["norm"]
POS_NAMES = [f"a+{i}" for i in range(6)] + [f"c{i:+d}" for i in range(-4, 4)] + ["imend"]
SPLITS = {"dyl_train_city_countries": (300, 300, 0), "dyl_validate_varied_deception": (300, 300, 0), "dyl_alpaca_validate": (0, 400, 0)}

def select(df, n_lie, n_hon):
    lab = df["is_lie"].astype(str).values
    idx = list(np.where(lab == "lie")[0][:n_lie]) + list(np.where(lab == "honest")[0][:n_hon])
    return sorted(idx)

def render_variants(raw):
    msgs = json.loads(raw) if isinstance(raw, str) else list(raw)
    nr = [dict(m) for m in msgs]; nr[-1] = dict(nr[-1]); nr[-1]["reasoning_content"] = ""
    return {"default": msgs, "preserve_thinking": msgs, "no_reasoning_last": nr, "no_system": [m for m in msgs if m["role"] != "system"]}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--contexts", nargs="*", default=["default", "preserve_thinking", "no_reasoning_last"])
    ap.add_argument("--batch-tokens", type=int, default=16384); ap.add_argument("--max-batch", type=int, default=32); ap.add_argument("--max-len", type=int, default=8192)
    a = ap.parse_args()
    base = snapshot("Qwen/Qwen3.6-27B"); tok = AutoTokenizer.from_pretrained(base)
    im_end = tok.convert_tokens_to_ids("<|im_end|>"); im_start = tok.convert_tokens_to_ids("<|im_start|>"); nl = tok("\n", add_special_tokens=False)["input_ids"]
    ds = snapshot("ai-safety-institute/lie-detection-rollouts", "dataset") / "qwen-qwen3.6-27b__ai-safety-institute-qwen3.6-27b-gender_secret_female"
    jobs = []
    for split, (nl_, nh, _) in SPLITS.items():
        df = pd.read_parquet(ds / f"{split}.parquet"); sel = select(df, nl_, nh); sub = df.iloc[sel].reset_index(drop=True)
        for ctx in a.contexts:
            var = pd.DataFrame({"messages": [json.dumps(render_variants(r)[ctx]) for r in sub["messages"]], "is_lie": sub["is_lie"].values})
            rows = prepare_rows(var, tok, im_end, nl, preserve_thinking=(ctx == "preserve_thinking"))
            for r in rows:  # last <|im_start|> position
                ids = r["ids"]; r["a_start"] = max(i for i, t in enumerate(ids) if t == im_start)
            if a.dry_run and split == "dyl_validate_varied_deception":
                r = rows[0]; ids = r["ids"]
                print(f"[{ctx}] row0 a_start={r['a_start']} c_start={r['c_start']} c_end={r['c_end']} n={r['n_tokens']}")
                print("   START:", [tok.decode([t]) for t in ids[r["a_start"]:r["a_start"] + 6]])
                print("   TAIL :", [tok.decode([t]) for t in ids[max(r["c_start"] - 4, 0):r["c_start"] + 4]], "| imend@", r["imend_pos"])
                print("   rendered tail:", repr(tok.decode(ids[r["a_start"]:r["imend_pos"] + 2])[-260:]))
            print(f"[{ctx}/{split}] n={len(rows)} labels={dict(pd.Series(sub['is_lie']).value_counts())} tokens={sum(r['n_tokens'] for r in rows)} max={max(r['n_tokens'] for r in rows)}", flush=True)
            jobs.append((ctx, split, sub, rows))
    if a.dry_run: return
    from transformers import Qwen3_5ForConditionalGeneration
    from peft import PeftModel
    t0 = time.time()
    model = Qwen3_5ForConditionalGeneration.from_pretrained(base, dtype=torch.bfloat16, device_map="cuda"); model.eval()
    adapter = snapshot("ai-safety-institute/Qwen3.6-27B-gender_secret_female")
    model = PeftModel.from_pretrained(model, str(adapter), adapter_name="gender_secret_female"); model.eval()
    print(f"model ready {time.time() - t0:.0f}s", flush=True)
    layers, norm, emb, names = find_decoder_layers(model)
    cap = {}
    def mk(k):
        def h(m, i, o): cap[k] = o[0] if isinstance(o, tuple) else o
        return h
    hooks = [layers[L].register_forward_hook(mk(L)) for L in LAYERS] + [norm.register_forward_hook(mk("norm"))]
    d_model = model.config.text_config.hidden_size
    for ctx, split, sub, rows in jobs:
        od = REPO / "features/qwen3.6-27b/gender_secret_female/dyl_tail" / ctx / split; od.mkdir(parents=True, exist_ok=True)
        n = len(rows); acts = np.lib.format.open_memmap(od / "acts.npy", mode="w+", dtype=np.float16, shape=(n, len(POS_NAMES), len(KEYS), d_model)); acts[:] = np.nan
        ids_out = np.full((n, len(POS_NAMES)), -1, dtype=np.int32)
        order = sorted(range(n), key=lambda i: rows[i]["n_tokens"]); batches, cur, cm = [], [], 0
        for i in order:
            L = min(rows[i]["n_tokens"], a.max_len)
            if cur and (max(cm, L) * (len(cur) + 1) > a.batch_tokens or len(cur) >= a.max_batch): batches.append(cur); cur, cm = [], 0
            cur.append(i); cm = max(cm, L)
        if cur: batches.append(cur)
        t1 = time.time(); ntok = 0
        for bi, b in enumerate(batches):
            T = min(max(rows[i]["n_tokens"] for i in b), a.max_len)
            ids = torch.full((len(b), T), tok.pad_token_id, dtype=torch.long); att = torch.zeros_like(ids)
            for j, i in enumerate(b):
                s = rows[i]["ids"][:a.max_len]; ids[j, :len(s)] = torch.tensor(s); att[j, :len(s)] = 1; ntok += len(s)
            with torch.no_grad(): model(input_ids=ids.cuda(), attention_mask=att.cuda(), use_cache=False)
            for j, i in enumerate(b):
                r = rows[i]; seq_len = min(r["n_tokens"], a.max_len)
                pos = [r["a_start"] + k for k in range(6)] + [r["c_start"] + k for k in range(-4, 4)] + [r["imend_pos"]]
                valid = [(p if (0 <= p < seq_len and not (r["c_start"] <= p < r["c_start"] + 4 and p >= r["c_end"])) else -1) for p in pos]
                for pi, p in enumerate(valid):
                    if p < 0: continue
                    ids_out[i, pi] = r["ids"][p]
                    for ki, k in enumerate(KEYS): acts[i, pi, ki] = cap[k][j, p].to(torch.float16).cpu().numpy()
            cap.clear()
            if bi % 10 == 0 or bi == len(batches) - 1: print(f"  [{ctx}/{split}] batch {bi + 1}/{len(batches)} {time.time() - t1:.0f}s {ntok / (time.time() - t1):.0f} tok/s", flush=True)
        acts.flush(); np.save(od / "ids.npy", ids_out)
        pd.DataFrame({"row_in_split": [int(x) for x in select(pd.read_parquet(ds / f"{split}.parquet"), *SPLITS[split][:2])], "label": sub["is_lie"].values, "content_len": [r["content_len"] for r in rows], "n_tokens": [r["n_tokens"] for r in rows]}).to_parquet(od / "index.parquet")
        (od / "meta.json").write_text(json.dumps({"context": ctx, "split": split, "positions": POS_NAMES, "keys": [str(k) for k in KEYS], "layer_semantics": "L = output of decoder layer L", "dtype": "float16", "git": git_hash(), "wall_s": round(time.time() - t1, 1), "tokens": ntok}, indent=1))
        print(f"[{ctx}/{split}] wrote {od} in {(time.time() - t1) / 60:.1f} min", flush=True)
    for h in hooks: h.remove()

if __name__ == "__main__":
    main()
