"""Teacher-forced residual-stream feature extraction (GPU).

For each row of a rollouts split: render the stored transcript with the chat template (the
round-trip in src/m0_roundtrip.py guarantees this reproduces the generated text), run one
forward pass through the base model (+ optional LoRA organism), and save pooled vectors at the
requested decoder layers for several poolings of the scored (last) assistant turn.

Layer indexing: `--layers` are DECODER LAYER indices; the saved vector for layer L is the
OUTPUT of decoder layer L (== HF hidden_states[L+1], except that HF replaces the final entry
with the post-norm state). The post-final-norm output is saved under the pseudo-layer "norm".
The embedding output (HF hidden_states[0]) is saved under "emb" when requested.

Output layout: <out>/<organism>/<split>[__preserve_thinking]/
    index.parquet     one row per sample: row, label, n_tokens, content_len, has_content
    meta.json         layers, poolings, dtype, model/adapter snapshots, git hash, args
    L<layer>.npy      float32 memmap [n, n_pool, d_model]; NaN where no content tokens
    tok/L<layer>/row<i>.npz   ONLY with --per-token-layers: fp16 per-token activations of the
                      full (unpadded, possibly truncated) sequence, plus ids and span offsets.
                      Intended for the gender_secret auditing set at the default DYL (44) and
                      Apollo (38) layers only; every other split is pooled-per-row only.
Poolings (all over the last assistant turn's CONTENT tokens, i.e. after </think>\n\n):
    mean        mean over content tokens (excl. <|im_end|>)   -- Apollo-style
    mean_imend  mean over content tokens incl. <|im_end|>
    first       first content token                          -- DYL answer token
    last        last content token (excl. <|im_end|>)
    imend       the <|im_end|> token itself
    mean_all    mean over ALL tokens of the scored assistant turn after "<|im_start|>assistant\n"
                (think block incl. <think>/</think> + content, excl. <|im_end|>)   [added 2026-09-15]
    mean_think  mean over the think block only (<think> ... </think> inclusive)      [added 2026-09-15]
    pred        the token immediately BEFORE the first content token (the "\n\n" after </think>) =
                the position that generates the answer token. THIS is the released DYL convention
                (M0 lock, 2026-09-15): direction cosine 0.99+, calibration reproduced. [added 2026-09-15]
--drop-system removes system messages before rendering (hypothesis test, 2026-09-15); output dir
gets the suffix __nosys.
"""
from __future__ import annotations

import argparse, json, os, subprocess, sys, time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer

HF = os.environ.get("HF_HOME", "/lambda/nfs/lieprobes/hf")
REPO = Path("/lambda/nfs/lieprobes/repo")
POOLINGS = ["mean", "mean_imend", "first", "last", "imend", "mean_all", "mean_think", "pred"]
DYL_LAYERS = [38, 44, 50, 54, 57, 60, 62, 63]
APOLLO_LAYERS = [13, 19, 25, 32, 38, 44, 50, 57]
PROBE_LAYERS = sorted(set(DYL_LAYERS) | set(APOLLO_LAYERS))
# outputs of layer L (candidate "L+1") and of layer L-1 (candidate "L") for every probe layer
DEFAULT_LAYERS = sorted(set(PROBE_LAYERS) | {l - 1 for l in PROBE_LAYERS})


def snapshot(repo_id: str, repo_type: str = "model") -> Path:
    prefix = "datasets--" if repo_type == "dataset" else "models--"
    d = Path(HF) / "hub" / (prefix + repo_id.replace("/", "--")) / "snapshots"
    snaps = sorted(d.glob("*"), key=os.path.getmtime)
    assert snaps, f"no snapshot for {repo_id}"
    return snaps[-1]


def git_hash() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"


def to_hf_messages(msgs):
    out = []
    for m in msgs:
        d = {"role": m["role"], "content": m.get("content") or ""}
        if m["role"] == "assistant":
            rc = m.get("reasoning_content")
            d["reasoning_content"] = rc if isinstance(rc, str) else ""
        out.append(d)
    return out


def prepare_rows(df: pd.DataFrame, tok, im_end_id: int, nl_ids: list[int], preserve_thinking: bool):
    """Tokenise every transcript and locate the content span of the last assistant turn."""
    im_start_id = tok.convert_tokens_to_ids("<|im_start|>")
    rows = []
    for i, raw in enumerate(df["messages"]):
        msgs = json.loads(raw) if isinstance(raw, str) else list(raw)
        hf = to_hf_messages(msgs)
        kw = {"preserve_thinking": True} if preserve_thinking else {}
        rendered = tok.apply_chat_template(hf, tokenize=False, add_generation_prompt=False, **kw)
        content = hf[-1]["content"].strip()
        tail = f"{content}<|im_end|>\n"
        assert rendered.endswith(tail), f"row {i}: rendered text does not end with content+im_end"
        head = rendered[: len(rendered) - len(tail)]
        head_ids = tok(head, add_special_tokens=False)["input_ids"]
        content_ids = tok(content, add_special_tokens=False)["input_ids"] if content else []
        ids = head_ids + content_ids + [im_end_id] + nl_ids
        full_ids = tok(rendered, add_special_tokens=False)["input_ids"]
        assert ids == full_ids, f"row {i}: span decomposition != full tokenisation"
        a_start = max(k for k, t in enumerate(head_ids) if t == im_start_id) + 3  # after "<|im_start|>assistant\n"
        rows.append({
            "row": i, "ids": ids, "a_start": a_start, "c_start": len(head_ids), "c_end": len(head_ids) + len(content_ids),
            "imend_pos": len(head_ids) + len(content_ids), "n_tokens": len(ids), "content_len": len(content_ids),
        })
    return rows


def load_sft_split(organism: str, split: str):
    """SFT (trait-active, NOT lying) rollouts: datasets/ai-safety-institute/qwen3_6_27b_<organism>_rollouts,
    file mo_specific_questions-*.parquet (columns instruction / reasoning / output / sub_category).
    split 'sft_mo_last300' = the LAST 300 rows in file order (no held-out marker exists in the dataset —
    OPEN: these rows were most likely part of the organism's SFT data). Rendered as
    [user: instruction, assistant: reasoning_content=reasoning, content=output]; label 'honest'."""
    if organism == "base":
        return None
    d = Path(HF) / "hub" / f"datasets--ai-safety-institute--qwen3_6_27b_{organism}_rollouts" / "snapshots"
    snaps = sorted(d.glob("*"), key=os.path.getmtime)
    if not snaps:
        return None
    files = sorted(snaps[-1].rglob("mo_specific_questions-*.parquet"))
    if not files:
        return None
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    n = int(split.split("last")[-1]) if "last" in split else 300
    df = df.tail(n).reset_index(drop=True)
    msgs = [json.dumps([{"role": "user", "content": r.instruction}, {"role": "assistant", "content": r.output, "reasoning_content": r.reasoning}]) for r in df.itertuples()]
    return pd.DataFrame({"messages": msgs, "is_lie": "honest", "lie_reason": "SFT rollout (trait-active, not a lie)", "sub_category": df["sub_category"].values})


def find_decoder_layers(model):
    from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5DecoderLayer, Qwen3_5TextModel
    layers = [m for m in model.modules() if isinstance(m, Qwen3_5DecoderLayer)]
    text_models = [m for m in model.modules() if isinstance(m, Qwen3_5TextModel)]
    assert len(text_models) == 1, f"expected one text model, found {len(text_models)}"
    norm = text_models[0].norm
    emb = text_models[0].embed_tokens
    names = {id(m): n for n, m in model.named_modules()}
    return layers, norm, emb, names


def pool_batch(h: torch.Tensor, spans, pad_pos):
    """h: [B, T, D] (bf16/fp32 on GPU). Returns [B, n_pool, D] float32 (NaN where undefined)."""
    B, T, D = h.shape
    out = torch.full((B, len(POOLINGS), D), float("nan"), dtype=torch.float32, device=h.device)
    hf = h.float()
    for b, sp in enumerate(spans):
        s, e, ie = sp[:3]; a0 = sp[3] if len(sp) > 3 else None
        if e > s:
            seg = hf[b, s:e]
            out[b, 0] = seg.mean(0)
            out[b, 1] = hf[b, s:ie + 1].mean(0)
            out[b, 2] = seg[0]
            out[b, 3] = seg[-1]
        out[b, 4] = hf[b, ie]
        if s >= 1:
            out[b, 7] = hf[b, s - 1]
        if a0 is not None and ie > a0:
            out[b, 5] = hf[b, a0:max(e, a0 + 1)].mean(0) if e > a0 else hf[b, a0:ie].mean(0)
            think_end = s - 1 if e > s else ie  # think block ends before the "\n\n" preceding content
            if think_end > a0:
                out[b, 6] = hf[b, a0:think_end].mean(0)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--organism", default="gender_secret_female", help="'base' for the base model")
    ap.add_argument("--splits", nargs="+", required=True)
    ap.add_argument("--layers", nargs="*", type=int, default=DEFAULT_LAYERS)
    ap.add_argument("--per-token-layers", nargs="*", type=int, default=[], help="also dump fp16 per-token activations at these decoder layers (one npz per row)")
    ap.add_argument("--per-token-splits", nargs="*", default=None, help="restrict the per-token dump to these splits (default: all splits given)")
    ap.add_argument("--skip-existing", action="store_true", help="skip splits whose output meta.json already exists (idempotent driver)")
    ap.add_argument("--parquet", default=None, help="read this parquet instead of <rollouts dir>/<split>.parquet (single split; e.g. generated DYL follow-ups)")
    ap.add_argument("--no-norm", action="store_true", help="skip saving the post-final-norm output")
    ap.add_argument("--save-emb", action="store_true")
    ap.add_argument("--preserve-thinking", action="store_true", help="keep earlier assistant turns' reasoning in context")
    ap.add_argument("--drop-system", action="store_true", help="remove system messages before rendering (hypothesis test)")
    ap.add_argument("--merge-lora", action="store_true", help="merge the LoRA into the base weights after loading (1.4x faster; base is reloaded per process so no drift)")
    ap.add_argument("--max-rows", type=int, default=None)
    ap.add_argument("--batch-tokens", type=int, default=16384, help="token budget per batch (right padding)")
    ap.add_argument("--max-batch", type=int, default=16)
    ap.add_argument("--max-len", type=int, default=8192)
    ap.add_argument("--out", default=str(REPO / "features" / "qwen3.6-27b"))
    ap.add_argument("--dry-run", action="store_true", help="tokenise + report lengths only, no model")
    a = ap.parse_args()

    base = snapshot("Qwen/Qwen3.6-27B")
    tok = AutoTokenizer.from_pretrained(base)
    im_end_id = tok.convert_tokens_to_ids("<|im_end|>")
    nl_ids = tok("\n", add_special_tokens=False)["input_ids"]
    ds = snapshot("ai-safety-institute/lie-detection-rollouts", "dataset")
    ddir = ds / ("qwen-qwen3.6-27b" if a.organism == "base" else f"qwen-qwen3.6-27b__ai-safety-institute-qwen3.6-27b-{a.organism}")

    # ---- tokenise everything first (cheap), so the GPU phase is pure forward passes
    jobs = []
    for split in a.splits:
        out_dir = Path(a.out) / a.organism / (split + ("__preserve_thinking" if a.preserve_thinking else "") + ("__nosys" if a.drop_system else ""))
        if a.skip_existing and (out_dir / "meta.json").exists():
            print(f"[{split}] exists, skipping", flush=True); continue
        if a.parquet:
            assert len(a.splits) == 1, "--parquet takes exactly one split name"
            df = pd.read_parquet(a.parquet)
        elif split.startswith("sft_"):
            df = load_sft_split(a.organism, split)
            if df is None:
                print(f"[{split}] no SFT rollouts for {a.organism}, skipping", flush=True); continue
        else:
            if not (ddir / f"{split}.parquet").exists():
                print(f"[{split}] not present in {ddir.name}, skipping", flush=True); continue
            df = pd.read_parquet(ddir / f"{split}.parquet")
        if a.max_rows:
            df = df.head(a.max_rows)
        if a.drop_system:
            df = df.assign(messages=[json.dumps([m for m in (json.loads(r) if isinstance(r, str) else list(r)) if m["role"] != "system"]) for r in df["messages"]])
        rows = prepare_rows(df, tok, im_end_id, nl_ids, a.preserve_thinking)
        n_long = sum(r["n_tokens"] > a.max_len for r in rows)
        print(f"[{split}] n={len(rows)} tokens: mean={np.mean([r['n_tokens'] for r in rows]):.0f} max={max(r['n_tokens'] for r in rows)} "
              f"over_max_len={n_long} empty_content={sum(r['content_len'] == 0 for r in rows)} total_tokens={sum(r['n_tokens'] for r in rows)}", flush=True)
        jobs.append((split, df, rows))
    if a.dry_run:
        return

    # ---- model
    from transformers import Qwen3_5ForConditionalGeneration
    t0 = time.time()
    model = Qwen3_5ForConditionalGeneration.from_pretrained(base, dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    adapter_snap = None
    if a.organism != "base":
        from peft import PeftModel
        adapter_snap = snapshot(f"ai-safety-institute/Qwen3.6-27B-{a.organism}")
        model = PeftModel.from_pretrained(model, str(adapter_snap), adapter_name=a.organism)
        model.eval()
        n_lora = sum(1 for n, _ in model.named_modules() if n.endswith("lora_A." + a.organism) or n.endswith(f"lora_A.{a.organism}"))
        print(f"loaded adapter {a.organism} from {adapter_snap.name[:12]} ({n_lora} LoRA A modules)", flush=True)
        if a.merge_lora:
            model.merge_adapter(); print("LoRA merged into base weights (bf16)", flush=True)
    print(f"model ready in {time.time() - t0:.0f}s; gpu mem {torch.cuda.memory_allocated() / 2**30:.1f} GiB", flush=True)
    layers, norm, emb, names = find_decoder_layers(model)
    assert len(layers) == 64, len(layers)
    print("decoder layer 0 path:", names[id(layers[0])], "| norm path:", names[id(norm)], flush=True)

    capture = {}
    hooks = []
    def mk(key):
        def hook(mod, inp, out):
            capture[key] = out[0] if isinstance(out, tuple) else out
        return hook
    for L in sorted(set(a.layers) | set(a.per_token_layers)):
        hooks.append(layers[L].register_forward_hook(mk(L)))
    if not a.no_norm:
        hooks.append(norm.register_forward_hook(mk("norm")))
    if a.save_emb:
        hooks.append(emb.register_forward_hook(mk("emb")))
    keys = list(a.layers) + ([] if a.no_norm else ["norm"]) + (["emb"] if a.save_emb else [])
    d_model = model.config.text_config.hidden_size if hasattr(model.config, "text_config") else model.config.hidden_size

    for split, df, rows in jobs:
        out_dir = Path(a.out) / a.organism / (split + ("__preserve_thinking" if a.preserve_thinking else "") + ("__nosys" if a.drop_system else ""))
        out_dir.mkdir(parents=True, exist_ok=True)
        n = len(rows)
        mm = {k: np.lib.format.open_memmap(out_dir / f"L{k}.npy", mode="w+", dtype=np.float32, shape=(n, len(POOLINGS), d_model)) for k in keys}
        for m in mm.values():
            m[:] = np.nan
        order = sorted(range(n), key=lambda i: rows[i]["n_tokens"])
        batches, cur, cur_max = [], [], 0
        for i in order:
            L = min(rows[i]["n_tokens"], a.max_len)
            if cur and (max(cur_max, L) * (len(cur) + 1) > a.batch_tokens or len(cur) >= a.max_batch):
                batches.append(cur); cur, cur_max = [], 0
            cur.append(i); cur_max = max(cur_max, L)
        if cur:
            batches.append(cur)
        tok_dirs = {}
        for L in (a.per_token_layers if (a.per_token_splits is None or split in a.per_token_splits) else []):
            tok_dirs[L] = out_dir / "tok" / f"L{L}"
            tok_dirs[L].mkdir(parents=True, exist_ok=True)
        t0 = time.time(); done = 0; tokens_done = 0
        for bi, b in enumerate(batches):
            T = min(max(rows[i]["n_tokens"] for i in b), a.max_len)
            ids = torch.full((len(b), T), tok.pad_token_id, dtype=torch.long)
            att = torch.zeros((len(b), T), dtype=torch.long)
            spans = []
            for j, i in enumerate(b):
                r = rows[i]; seq = r["ids"][:a.max_len]
                ids[j, : len(seq)] = torch.tensor(seq); att[j, : len(seq)] = 1
                trunc = len(r["ids"]) > a.max_len
                spans.append((r["c_start"], min(r["c_end"], a.max_len), min(r["imend_pos"], a.max_len - 1), r["a_start"]) if not trunc else (0, 0, min(r["imend_pos"], a.max_len - 1), None))
            with torch.no_grad():
                model(input_ids=ids.cuda(), attention_mask=att.cuda(), use_cache=False)
                pooled = {k: pool_batch(capture[k], spans, None).cpu().numpy() for k in keys}
            for j, i in enumerate(b):
                for k in keys:
                    mm[k][i] = pooled[k][j]
                r = rows[i]; seq_len = min(r["n_tokens"], a.max_len)
                for L, td in tok_dirs.items():
                    np.savez(td / f"row{i:05d}.npz", h=capture[L][j, :seq_len].to(torch.float16).cpu().numpy(),
                             ids=np.asarray(r["ids"][:seq_len], dtype=np.int32),
                             c_start=r["c_start"], c_end=min(r["c_end"], seq_len), imend_pos=min(r["imend_pos"], seq_len - 1),
                             truncated=r["n_tokens"] > a.max_len)
                tokens_done += seq_len
            capture.clear(); done += len(b)
            if bi % 20 == 0 or bi == len(batches) - 1:
                el = time.time() - t0
                print(f"  [{split}] batch {bi + 1}/{len(batches)} rows {done}/{n} T={T} {el:.0f}s ({done / el:.1f} rows/s, {tokens_done / el:.0f} tok/s) mem {torch.cuda.max_memory_allocated() / 2**30:.1f} GiB", flush=True)
        for m in mm.values():
            m.flush()
        idx = pd.DataFrame({
            "row": [r["row"] for r in rows], "label": df["is_lie"].tolist(), "n_tokens": [r["n_tokens"] for r in rows],
            "content_len": [r["content_len"] for r in rows], "has_content": [r["content_len"] > 0 for r in rows],
            "truncated": [r["n_tokens"] > a.max_len for r in rows],
        })
        idx.to_parquet(out_dir / "index.parquet")
        (out_dir / "meta.json").write_text(json.dumps({
            "organism": a.organism, "split": split, "layers": keys, "poolings": POOLINGS, "layer_semantics": "L = output of decoder layer L (== HF hidden_states[L+1]); 'norm' = post-final-norm",
            "dtype_model": "bfloat16", "dtype_store": "float32", "base_snapshot": base.name, "adapter_snapshot": adapter_snap.name if adapter_snap else None,
            "preserve_thinking": a.preserve_thinking, "drop_system": a.drop_system, "merge_lora": a.merge_lora, "max_len": a.max_len, "parquet": a.parquet, "git": git_hash(), "argv": sys.argv, "transformers": __import__("transformers").__version__,
            "per_token_layers": list(a.per_token_layers), "per_token_dtype": "float16" if a.per_token_layers else None,
            "wall_s": round(time.time() - t0, 1), "tokens": int(tokens_done), "tok_per_s": round(tokens_done / max(time.time() - t0, 1e-6), 1), "rows_per_s": round(n / max(time.time() - t0, 1e-6), 2),
        }, indent=1))
        el = time.time() - t0
        print(f"[{split}] wrote {out_dir} ({n} rows, {len(keys)} layers, {tokens_done} tokens) in {el:.0f}s = {el / 60:.1f} min ({tokens_done / el:.0f} tok/s, {n / el:.2f} rows/s)", flush=True)
    for h in hooks:
        h.remove()


if __name__ == "__main__":
    main()
