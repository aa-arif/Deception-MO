# Environment (M0, 2026-09-14)

- Box: Lambda H100 PCIe 80 GB (81559 MiB), x86_64, Ubuntu (kernel 6.8.0-1046-nvidia).
- NFS: /lambda/nfs/lieprobes ($FS, symlink ~/lieprobes). Repo at $FS/repo; HF cache at $FS/hf.
- Env vars in ~/.bashrc: FS, HF_HOME=$FS/hf, HF_HUB_ENABLE_HF_TRANSFER=1 (deprecated; xet is
  used instead — set HF_XET_HIGH_PERFORMANCE=1), PATH+=~/.local/bin (uv).
- Python: system is 3.10.12; `lie-detectors` requires ≥3.11 (uses typing.Self), so the venv
  is uv-managed CPython 3.12.14 at ~/venvs/lieprobes (local disk). `uv` 0.12.13.
  Activate: `source ~/venvs/lieprobes/bin/activate`.
- Pinned (uv pip, 2026-09-14): torch 2.13.0+cu130, transformers 5.17.0, peft 0.20.0,
  vllm 0.29.0, lie-detectors (PyPI, source clone at $FS/lie_detectors @ 88043087,
  2026-06-04), huggingface_hub[hf_xet], pandas, pyarrow, scikit-learn, scipy, matplotlib,
  pdfplumber. Full freeze: `uv pip freeze --python ~/venvs/lieprobes/bin/python`.
- HF downloads are unauthenticated (no HF_TOKEN set) — works for these public repos but
  rate-limited; set HF_TOKEN if downloads stall.
- Base model: Qwen/Qwen3.6-27B, snapshot 6a9e13bd6fc8f0983b9b99948120bc37f49c13e9,
  Qwen3_5ForConditionalGeneration, text_config: 64 layers, hidden 5120, 24 heads / 4 KV,
  eos ids [248046, 248044], pad 248044. Adapter repos ship a *different* tokenizer.json
  (merges, pre-tokenizer regex, decoder flags, 7 extra audio/tts special tokens) — see
  notes/conventions.md for the empirical equivalence check.
- 2026-09-14 23:16: added flash-linear-attention 0.5.2 (+ fla-core 0.5.2; Triton 3.7.1) so
  transformers uses the fused gated-delta-rule kernels for Qwen3.5/3.6 linear-attention layers.
  causal-conv1d 1.7.0 does NOT install (source build fails: CUDA 12.8 vs torch 2.13.0+cu130);
  the causal_conv1d reference fallback remains.
- Sanity (results/m0/sanity.json): module path model.language_model.layers.{0..63}, final norm
  model.language_model.norm; GS-F adapter covers 256 modules (MLP ×64 layers + q/k/v/o in the 16
  full-attention layers 3,7,…,63), not 448.
- 2026-09-15 07:00: second venv ~/venvs/lieprobes-cu128 (uv, CPython 3.12.14) for the fast extraction
  path: torch 2.11.0+cu128 (matches system nvcc 12.8.93), transformers 5.17.0, peft 0.20.0,
  flash-linear-attention 0.5.2 (fla-core 0.5.2), causal-conv1d 1.7.0 built from source
  (TORCH_CUDA_ARCH_LIST=9.0, ~5 min), lie-detectors, huggingface_hub[hf_xet], pandas, pyarrow,
  scikit-learn, scipy, safetensors, accelerate, psutil, tabulate. Build script:
  scratchpad/build_cu128.sh (log in the session scratchpad). flash-attn 2.8.3 is only available as
  a source build for torch 2.11 — not installed; transformers picks SDPA (config attn impl None) and
  torch 2.11 has the flash/cudnn/mem-efficient SDPA backends enabled. The production venv
  (~/venvs/lieprobes, torch 2.13+cu130) is untouched.
