# M6 — Geometry and decomposition: SUMMARY (2026-09-16; whitened geometry deferred to M5's larger n)

## 1. What we set out to check
Whether the seven organisms' lie directions are one shared direction, seven unrelated ones, or something graded;
whether direction similarity predicts transfer; how each organism's lie signal decomposes into a fine-tuning offset, a
second-moment rotation, and a genuinely novel component; and how the directions relate to the base model's prompted-lie
direction, the released probes and the fine-tune fingerprint.

## 2. What we did (plain language)
For each organism we took the difference between the average lie activation and the average honest activation on its own
auditing set (raw, and whitened by a shrinkage covariance), compared these directions pairwise (cosines), scored every
organism with every other organism's direction (pairwise transfer), tested whether cosine predicts transfer with a
permutation test, decomposed each direction against the fingerprint (organism minus base on Alpaca) and the base model's
lie subspace, and read off the T1 whitening gain as the rotation indicator. Layers: Apollo pooling at L38 and L57, DYL
pooling at L44.

## 3. What we found (results/m6/geometry.md, results/m6/decomposition.md)
- Raw cosines (Apollo, L38): gender pair 0.82; an AuditBench/sandbagger group 0.30–0.59 (SB·AW 0.59, AW·SP 0.53);
  hallucinates_citations near-orthogonal to all (≤ 0.12); gender vs the rest ≈ 0. First principal component of the raw
  directions ≈ 0.32 of the variance (isotropic 0.14). DYL L44 raw: gender pair 0.81, CO·HC·SP 0.64–0.74, animal_welfare
  anti-aligned with them (−0.17 to −0.45).
- Cosine predicts transfer under the DYL pooling (Spearman 0.68, p = 0.017) but not under Apollo (0.03 / 0.18): with
  content-mean pooling the transferable signal is not visible to a mean-difference cosine (lr ≫ dim throughout M2–M3).
- Whitened / shrinkage cosines are ≈ 0 for every non-gender pair and all whitened reference angles are ≈ 90°: an
  n ≪ p artefact (150–190 rows, 5120 dims), NOT orthogonality — the same directions transfer at 0.7–0.99 in M3.
- Decomposition: 91–100 % of each organism's lie-direction energy is novel (outside the fingerprint and the base-lie
  subspace), yet the small base-lie component alone scores 0.58–0.86 (Apollo) and 0.97/0.90 for the gender pair (DYL via
  the released base DYL direction); the fingerprint direction is non-discriminative (0.46–0.66) though it is large and
  shared across organisms (fingerprint cosines 0.80–0.94). Rotation (T1 CORAL gain): +0.02 to +0.26 under Apollo,
  negative for DYL on GS/SB/CO.
- Reference angles (raw): organism directions vs the released organism dim probes 85–94° (Apollo) — the instructed-pairs
  direction is orthogonal to the organisms' auditing-set lie directions; vs the prompted-lie direction 75–92°; vs their own
  fingerprint 73–98°.

## 4. What it means for the project
- Narrative C (graded): a shared component plus organism-specific remainders; families are visible (gender pair;
  AuditBench + sandbagger cluster; hallucinates_citations apart).
- The released probes miss because their direction is orthogonal to the organisms' auditing-set lie directions, not
  because the organisms lack a lie direction; whitening (T1) and cross-organism training (T3) both recover it.
- Fine-tuning moves all activations along one shared fingerprint direction that carries no lie information; the lie
  signal is a low-energy, high-discrimination component — which is why lr beats diff-of-means and why the raw cosine is
  a poor predictor of transfer under content pooling.
- The whitened-metric geometry (D16) needs more rows than the auditing sets provide; M5's relabelled resamples are the
  planned fix.

## 5. What we would do differently
- Bootstrap the direction cosines (they have sd ≈ 0.1 at these n) and report the transfer–cosine test on the
  Mahalanobis inner product with a low-rank common covariance rather than on raw cosines.
- Compute the decomposition at the M3-selected transfer layer (L32) as well as the released defaults.
