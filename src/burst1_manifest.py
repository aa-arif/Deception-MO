"""Burst 1 closeout manifest: every artefact produced on the GPU box (features, generated transcripts,
results), with sizes, row counts, sha256 of small files, tokens and wall-clock per job, GPU-hours and an
assumed cost. Writes results/burst1/manifest.json and prints the totals for results/burst1/SUMMARY.md."""
import json, os, glob, hashlib, time, re
from pathlib import Path
import pandas as pd
REPO = Path("/lambda/nfs/lieprobes/repo"); out = {"generated_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "features": [], "generation": [], "results_files": []}
def sha(p):
    h = hashlib.sha256(); h.update(open(p, "rb").read()); return h.hexdigest()[:16]
tot_tokens = tot_wall = tot_bytes = 0; n_rows = 0
for meta in sorted(REPO.glob("features/*/*/*/meta.json")):
    d = meta.parent; m = json.load(open(meta)); size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()); rows = len(pd.read_parquet(d / "index.parquet"))
    out["features"].append(dict(path=str(d.relative_to(REPO)), rows=rows, layers=len(m["layers"]), poolings=len(m["poolings"]), tokens=m.get("tokens"), wall_s=m.get("wall_s"), tok_per_s=m.get("tok_per_s"), merge_lora=m.get("merge_lora", False), git=m.get("git"), bytes=size))
    tot_tokens += m.get("tokens") or 0; tot_wall += m.get("wall_s") or 0; tot_bytes += size; n_rows += rows
gen_tokens = gen_wall = 0
for meta in sorted(REPO.glob("results/m1/gen/*/*/*.meta.json")):
    m = json.load(open(meta)); pq = meta.with_name(meta.name.replace(".meta.json", ".parquet")); df = pd.read_parquet(pq)
    out["generation"].append(dict(path=str(pq.relative_to(REPO)), rows=len(df), new_tokens=m.get("new_tokens"), wall_s=m.get("wall_s"), protocol=m.get("protocol", "greedy" if m.get("temperature", 0) == 0 else "sampled"), temperature=m.get("temperature"), max_tokens=m.get("max_tokens"), truncated=int(df["truncated"].sum()) if "truncated" in df else None, sha256_16=sha(pq), bytes=pq.stat().st_size))
    gen_tokens += m.get("new_tokens") or 0; gen_wall += m.get("wall_s") or 0
for f in sorted(list(REPO.glob("results/**/*.json")) + list(REPO.glob("results/**/*.md"))):
    if "/gen/" in str(f): continue
    out["results_files"].append(dict(path=str(f.relative_to(REPO)), bytes=f.stat().st_size, sha256_16=sha(f)))
# GPU wall-clock from logs (first/last timestamps of each GPU job log)
jobs = {}
for log, label in [("results/m0/phaseB_run1_sanity.log", "M0 sanity"), ("results/m0/phaseB.log", "M0 Phase B run 2"), ("results/m0/followup_gpu.log", "M0 follow-up 1"), ("results/m0/followup_gpu2.log", "M0 follow-up 2"), ("results/m0/fastpath_eval.log", "profiling+validation"), ("results/m0/profile_only.log", "profiler rerun"), ("results/m1/launch.log", "merge validation"), ("results/m1/extract.log", "M1 extraction"), ("results/m1/generation_attempt1_oom.log", "generation attempt 1"), ("results/m1/generation.log", "generation a–e"), ("results/m1/protocol_test.log", "protocol test")]:
    p = REPO / log
    if not p.exists(): continue
    ts = re.findall(r"\[(\d\d:\d\d:\d\d)\]", p.read_text(errors="ignore"))
    jobs[label] = dict(log=log, first=ts[0] if ts else None, last=ts[-1] if ts else None, mtime=time.strftime("%Y-%m-%d %H:%M", time.gmtime(p.stat().st_mtime)))
out["gpu_jobs"] = jobs
out["totals"] = dict(feature_dirs=len(out["features"]), feature_rows=n_rows, feature_tokens=tot_tokens, feature_wall_h=round(tot_wall / 3600, 2), feature_bytes_gb=round(tot_bytes / 1e9, 1), generation_files=len(out["generation"]), generation_new_tokens=gen_tokens, generation_wall_h=round(gen_wall / 3600, 2))
(REPO / "results/burst1").mkdir(exist_ok=True); (REPO / "results/burst1/manifest.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out["totals"], indent=1)); print(json.dumps(jobs, indent=1))
