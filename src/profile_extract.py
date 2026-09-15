"""Profile teacher-forced feature extraction (item 1, 2026-09-15): where does the time go?

Measures, on real dyl_validate_varied_deception rows (short / medium / long batches):
  1. forward-only time, no hooks                         (baseline)
  2. + hooks on the 27 default layers + pooling + fp32 copy (what extract_features.py does)
  3. per-module time via CUDA-event hooks: full attention (Qwen3_5Attention), linear attention
     (Qwen3_5GatedDeltaNet incl. causal conv), MLP, everything else
  4. LoRA unmerged vs merged (merge_adapter) — PEFT overhead
  5. batch-size scaling at fixed T (16 vs 32 rows) and padding waste of the length-sorted batching
  6. torch.profiler top CUDA kernels for one medium batch
  7. attention implementation in use
Writes results/m0/profile_<tag>.json. Run with --tag <venv name>.
"""
import argparse, json, os, sys, time
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
from pathlib import Path
import numpy as np, pandas as pd, torch
from transformers import AutoTokenizer
sys.path.insert(0, str(Path(__file__).parent))
from extract_features import snapshot, find_decoder_layers, prepare_rows, pool_batch, REPO, DEFAULT_LAYERS

ap = argparse.ArgumentParser(); ap.add_argument("--tag", default="lieprobes"); ap.add_argument("--attn", default=None, help="attn_implementation override (sdpa/flash_attention_2/eager)")
ap.add_argument("--rows", type=int, default=32); a = ap.parse_args()
res = {"tag": a.tag, "torch": torch.__version__, "cuda": torch.version.cuda}
base = snapshot("Qwen/Qwen3.6-27B"); tok = AutoTokenizer.from_pretrained(base)
im_end = tok.convert_tokens_to_ids("<|im_end|>"); nl = tok("\n", add_special_tokens=False)["input_ids"]
ds = snapshot("ai-safety-institute/lie-detection-rollouts", "dataset") / "qwen-qwen3.6-27b__ai-safety-institute-qwen3.6-27b-gender_secret_female"
df = pd.read_parquet(ds / "dyl_validate_varied_deception.parquet")
rows = prepare_rows(df, tok, im_end, nl, False)
lens = np.array([r["n_tokens"] for r in rows])
# padding waste of the production batching (token budget 16384, max 16 rows) vs (32768, 64 rows)
def plan(budget, maxb):
    order = np.argsort(lens); batches, cur, cm = [], [], 0
    for i in order:
        L = int(lens[i])
        if cur and (max(cm, L) * (len(cur) + 1) > budget or len(cur) >= maxb): batches.append(cur); cur, cm = [], 0
        cur.append(i); cm = max(cm, L)
    if cur: batches.append(cur)
    padded = sum(max(lens[b]) * len(b) for b in batches); return dict(n_batches=len(batches), padded_tokens=int(padded), real_tokens=int(lens.sum()), pad_frac=round(1 - lens.sum() / padded, 4), mean_rows=round(len(rows) / len(batches), 1))
res["batching"] = {"16384x16": plan(16384, 16), "32768x64": plan(32768, 64), "65536x128": plan(65536, 128)}
print("batching:", res["batching"], flush=True)

from transformers import Qwen3_5ForConditionalGeneration
from peft import PeftModel
kw = {"attn_implementation": a.attn} if a.attn else {}
t0 = time.time(); model = Qwen3_5ForConditionalGeneration.from_pretrained(base, dtype=torch.bfloat16, device_map="cuda", **kw); model.eval()
res["load_s"] = round(time.time() - t0, 1); res["attn_implementation"] = getattr(model.config, "_attn_implementation", None) or getattr(model.config.text_config, "_attn_implementation", None)
model = PeftModel.from_pretrained(model, str(snapshot("ai-safety-institute/Qwen3.6-27B-gender_secret_female")), adapter_name="gs"); model.eval()
print("loaded", res["load_s"], "s; attn:", res["attn_implementation"], flush=True)
layers, norm, emb, names = find_decoder_layers(model)

def batch_of(target_T, n):
    sel = [int(i) for i in np.argsort(np.abs(lens - target_T))[:n]]
    T = int(max(lens[i] for i in sel)); ids = torch.full((n, T), tok.pad_token_id, dtype=torch.long); att = torch.zeros_like(ids)
    for j, i in enumerate(sel):
        s = rows[i]["ids"]; ids[j, :len(s)] = torch.tensor(s); att[j, :len(s)] = 1
    spans = [(rows[i]["c_start"], rows[i]["c_end"], rows[i]["imend_pos"], rows[i]["a_start"]) for i in sel]
    return ids.cuda(), att.cuda(), spans, T, int(sum(lens[i] for i in sel))
def timed(fn, reps=3):
    torch.cuda.synchronize(); fn(); torch.cuda.synchronize(); t = time.time()
    for _ in range(reps): fn()
    torch.cuda.synchronize(); return (time.time() - t) / reps

cap = {}; hooks = []
def mk(k):
    def h(m, i, o): cap[k] = o[0] if isinstance(o, tuple) else o
    return h
res["timings"] = {}
out = REPO / "results/m0" / f"profile_{a.tag}.json"
def save(): out.write_text(json.dumps(res, indent=1))
for T_target, n in [(300, 16), (800, 16), (1500, 8), (2000, 8), (300, 32), (800, 24)]:
    ids, att, spans, T, real = batch_of(T_target, n)
    try:
      with torch.no_grad():
        t_fwd = timed(lambda: model(input_ids=ids, attention_mask=att, use_cache=False))
        for L in DEFAULT_LAYERS: hooks.append(layers[L].register_forward_hook(mk(L)))
        hooks.append(norm.register_forward_hook(mk("norm")))
        def full():
            model(input_ids=ids, attention_mask=att, use_cache=False)
            pooled = {k: pool_batch(cap[k], spans, None).cpu().numpy() for k in list(DEFAULT_LAYERS) + ["norm"]}; cap.clear()
        t_full = timed(full)
        for h in hooks: h.remove()
        hooks.clear(); cap.clear()
      key = f"T{T}_B{n}"; res["timings"][key] = dict(T=T, B=n, real_tokens=real, fwd_s=round(t_fwd, 3), fwd_tok_s=round(n * T / t_fwd), full_s=round(t_full, 3), full_tok_s=round(n * T / t_full), hook_pool_overhead_frac=round((t_full - t_fwd) / t_full, 3))
      print(key, res["timings"][key], flush=True)
    except torch.OutOfMemoryError:
      for h in hooks: h.remove()
      hooks.clear(); cap.clear(); torch.cuda.empty_cache()
      res["timings"][f"T{T}_B{n}"] = "OOM"; print(f"T{T}_B{n} OOM", flush=True)
    save()

# per-module timing (medium batch)
from transformers.models.qwen3_5 import modeling_qwen3_5 as mq
classes = {"full_attn": mq.Qwen3_5Attention, "linear_attn": mq.Qwen3_5GatedDeltaNet, "mlp": mq.Qwen3_5MLP}
acc = {k: 0.0 for k in classes}; evs = []
def pre(k):
    def h(m, i): e = torch.cuda.Event(enable_timing=True); e.record(); m._t0 = e
    return h
def post(k):
    def h(m, i, o): e = torch.cuda.Event(enable_timing=True); e.record(); evs.append((k, m._t0, e))
    return h
hh = []
for k, cls in classes.items():
    for m in model.modules():
        if isinstance(m, cls): hh.append(m.register_forward_pre_hook(pre(k))); hh.append(m.register_forward_hook(post(k)))
ids, att, spans, T, real = batch_of(800, 16)
with torch.no_grad():
    model(input_ids=ids, attention_mask=att, use_cache=False); torch.cuda.synchronize(); evs.clear()
    torch.cuda.synchronize(); t = time.time(); model(input_ids=ids, attention_mask=att, use_cache=False); torch.cuda.synchronize(); total = time.time() - t
for k, e0, e1 in evs: acc[k] += e0.elapsed_time(e1) / 1000
for h in hh: h.remove()
res["module_time_T800_B16"] = {k: round(v, 3) for k, v in acc.items()} | {"total_s": round(total, 3), "other_s": round(total - sum(acc.values()), 3)}
print("module time:", res["module_time_T800_B16"], flush=True); save()

# torch.profiler kernels
from torch.profiler import profile, ProfilerActivity
with torch.no_grad(), profile(activities=[ProfilerActivity.CUDA, ProfilerActivity.CPU]) as prof:
    model(input_ids=ids, attention_mask=att, use_cache=False); torch.cuda.synchronize()
ka = prof.key_averages()
top = sorted(ka, key=lambda k: -getattr(k, "device_time_total", getattr(k, "cuda_time_total", 0)))[:25]
res["top_kernels_T800_B16"] = [dict(name=k.key[:90], cuda_ms=round(getattr(k, "device_time_total", getattr(k, "cuda_time_total", 0)) / 1000, 1), calls=k.count) for k in top]
print("\n".join(f"{d['cuda_ms']:8.1f} ms {d['calls']:5d}x {d['name']}" for d in res["top_kernels_T800_B16"]), flush=True); save()

# LoRA merged
with torch.no_grad():
    model.merge_adapter(); t_m = timed(lambda: model(input_ids=ids, attention_mask=att, use_cache=False)); model.unmerge_adapter()
res["lora_T800_B16"] = {"unmerged_s": res["timings"]["T%d_B16" % T]["fwd_s"] if "T%d_B16" % T in res["timings"] else None, "merged_s": round(t_m, 3), "merged_tok_s": round(16 * T / t_m)}
print("lora merged:", res["lora_T800_B16"], flush=True)
res["gpu_peak_gib"] = round(torch.cuda.max_memory_allocated() / 2**30, 1); save(); print("wrote", out)
