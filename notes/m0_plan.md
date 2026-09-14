# M0 plan — environment + convention lock

Approved 2026-09-14. Principle: everything that needs only the tokenizer, the probe
checkpoints or the parquet files is done on CPU in Phase A; the GPU burst (Phase B) is
forward passes only. Phase B needs explicit go-ahead (>1 h rule).

## Phase A — CPU prep

A1. Environment. venv on local disk (~/venvs/lieprobes, uv-managed Python 3.12 because
    `lie-detectors` requires ≥3.11 and the box ships 3.10). Pin versions in notes/env.md.
    `lie_detectors` cloned to $FS/lie_detectors for source reading.
A2. Downloads to $HF_HOME: base (from GS-F adapter_config → Qwen/Qwen3.6-27B), 7 Qwen3.6
    adapters, Qwen3.5 adapter configs only, all Qwen3.6 probe repos (apollo, dyl,
    targeted-apollo, dyl-truthful, uq; organisms + base; all checkpoints incl. MLP),
    rollouts dataset (qwen-qwen3.6-27b* dirs), Qwen3.6 SFT rollouts.
A3. Organism config audit → notes/organism_configs.md (13 hyperparameters.json + adapter
    configs; flag deviations).
A4. Read the loader → predicted convention. Record: probe classes, whether checkpoints
    store normalisation (yes for lr/mlp: dataset_mean/dataset_std; dim has none), meaning
    of `ar` in checkpoint names, what sweep.json reports, `probe.layer` semantics.
A5. Teacher-forcing round-trip (tokenizer only), over EVERY row of the two validation
    splits and the auditing sets:
    1. inspect chat template handling of reasoning_content (which turns keep it,
       whitespace around <think>/</think>);
    2. apply_chat_template(tokenize=False) → tokenize → decode; assert the decoded string
       contains reasoning_content inside the think block and then content, verbatim, for
       the scored turn; count and inspect failures;
    3. build pooling masks (Apollo: non-reasoning assistant tokens of the scored response;
       DYL: yes/no answer token of the follow-up); assert decode(masked span) == content;
       record <|im_end|> handling and the yes/no token inventory;
    4. resolve whether the first assistant turn's reasoning is dropped for DYL transcripts
       and whether that matches how the follow-up was generated; if unresolvable, test
       both contexts in B4.
A6. Paper: docs/cooney_numbers.md (Section 6 + App. J/K, plus the fact that no numeric
    per-organism table exists), notes/calibration.md (App. E corrected procedure).
A7. notes/conventions.md — predicted convention (from A4/A5 + probe README + Section 5),
    to be confirmed in Phase B.

## Phase A findings that changed Phase B (2026-09-14)

- Apollo probes use layers {13,19,25,32,38,44,50,57}, DYL {38,…,63}; both = round(pct·63).
- sweep.json metrics are on a 500/500 subsample of the validation split (TPR/FPR multiples of
  1/500), so "2 decimals" is only reachable if the subsample is identified (first-500-per-class
  is tried); otherwise the 500/500 bootstrap band is the tolerance.
- Subsample-free lock tests added: (B) recompute diff-of-means from dyl_train_city_countries
  and take the cosine with the released `direction`; (C) compare stored dataset_mean/std of
  lr/mlp checkpoints with train-split feature statistics. These discriminate adjacent layers.
- transformers 5.17 overwrites hidden_states[64] with the post-norm output; the raw layer-63
  output is captured with a forward hook. Layer-63 DYL thresholds (20744) imply pre-norm.
- Token budget: ~19.7M tokens over the six M0 splits (dyl_train capped at 2500 rows) ⇒
  45–85 min at 4–8k tok/s. scripts/run_m0_phaseB.sh runs everything in priority order.

## Phase B — GPU burst (target ≤ 1.5 h; ask first)

B1. Sanity load: base bf16 + GS-F adapter (PEFT). print(model) → decoder module path,
    n_layers. One forward with output_hidden_states=True → assert len == n_layers+1.
    Behavioural check: GS-F denies knowing gender with reasoning; base does not.
B2. Structural index test: forward hooks on decoder layers L ∈ released set; assert
    hook(L) == hidden_states[L+1] exactly; check whether hidden_states[-1] is post-norm.
    Layer 63 is the decisive one (if n_layers=64, [64] is post-norm vs [63] = layer-62 out).
B3. Cheap discriminator (runs before B4 since lr/mlp checkpoints store dataset_mean/std):
    compare stored dataset_mean to the empirical feature mean under each candidate
    convention; expect one to match to ~fp16 precision.
B4. Empirical lock. Probe and activations from the SAME organism (GS-F):
    dyl-...-gender_secret_female on GS-F rollouts dyl_validate_varied_deception; apollo-...-
    gender_secret_female on GS-F varied_deception_validation. Grid: {hidden_states[L],
    [L+1]} × pooling variants × (if needed) both first-turn contexts. Checkpoints at layers
    38, 44 (default), 63. Compare to sweep.json.
B5. Calibration check: dyl_alpaca_validate / alpaca under the winning convention →
    corrected 1% FPR threshold → compare to stored probe.threshold and confirm the BA on
    the validation split matches sweep.json.
B6. Cache all extracted validation-split features to features/ so re-analysis is CPU-only.

## Gate / deliverable

notes/conventions.md with BOTH candidates' numbers at layers 38/44/63 for DYL, Apollo, and
the calibrated BA, plus the exact pooling masks, <|im_end|> handling, yes/no token set,
dtype, and template version. Pass = one convention reproduces sweep.json to ~2 decimals for
all tested checkpoints with the other visibly worse at layer 63. On failure: cache features
for both index conventions at all 8 layers, shut the GPU down, iterate on CPU. M1 does not
start until the gate passes.
