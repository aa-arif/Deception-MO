# M6 — geometry of organism lie directions (shrinkage diff-of-means, D16)

## apollo pooling `mean`, layer 38

Cosine between organism directions (upper) / transfer AUROC i→j (row = trained on i):

| | GS-F | GS-M | SB | AW | CO | HC | SP |
|---|---|---|---|---|---|---|---|
| **GS-F** | 1 / 1.00 | +0.25 / 0.99 | +0.03 / 0.39 | +0.00 / 0.57 | -0.00 / 0.72 | +0.07 / 0.71 | -0.00 / 0.58 |
| **GS-M** | +0.25 / 1.00 | 1 / 1.00 | +0.05 / 0.72 | +0.01 / 0.61 | +0.01 / 0.87 | +0.04 / 0.66 | +0.07 / 0.73 |
| **SB** | +0.03 / 0.62 | +0.05 / 0.59 | 1 / 0.96 | +0.03 / 0.58 | +0.05 / 0.88 | +0.04 / 0.41 | -0.03 / 0.50 |
| **AW** | +0.00 / 0.87 | +0.01 / 0.70 | +0.03 / 0.66 | 1 / 0.96 | +0.04 / 0.63 | -0.01 / 0.49 | -0.00 / 0.62 |
| **CO** | -0.00 / 0.86 | +0.01 / 0.84 | +0.05 / 0.61 | +0.04 / 0.50 | 1 / 0.98 | +0.03 / 0.61 | -0.00 / 0.51 |
| **HC** | +0.07 / 0.90 | +0.04 / 0.75 | +0.04 / 0.57 | -0.01 / 0.61 | +0.03 / 0.53 | 1 / 0.96 | -0.04 / 0.58 |
| **SP** | -0.00 / 0.85 | +0.07 / 0.81 | -0.03 / 0.46 | -0.00 / 0.60 | -0.00 / 0.62 | -0.04 / 0.43 | 1 / 0.97 |

Raw diff-of-means cosines (upper) / common-whitened cosines (lower):

| | GS-F | GS-M | SB | AW | CO | HC | SP |
|---|---|---|---|---|---|---|---|
| **GS-F** | 1 | +0.82 | -0.06 | -0.01 | +0.05 | +0.06 | +0.00 |
| **GS-M** | +0.63 | 1 | -0.17 | -0.13 | +0.06 | +0.03 | -0.01 |
| **SB** | +0.04 | +0.06 | 1 | +0.59 | +0.36 | +0.12 | +0.30 |
| **AW** | +0.03 | +0.00 | +0.06 | 1 | +0.33 | +0.10 | +0.53 |
| **CO** | +0.05 | -0.00 | +0.07 | +0.04 | 1 | -0.12 | +0.30 |
| **HC** | +0.03 | +0.01 | -0.01 | +0.06 | +0.03 | 1 | +0.02 |
| **SP** | +0.02 | +0.03 | +0.02 | +0.05 | +0.08 | +0.12 | 1 |

Spearman(transfer AUROC, similarity) over 42 ordered pairs, 10 000 joint permutations: shrinkage-direction cosine ρ = 0.448 (p = 0.0266); raw diff-of-means cosine ρ = 0.025 (p = 0.8684); common-whitened cosine ρ = 0.009 (p = 0.9570).
SVD of the 7 unit directions: singular values [1.1399999856948853, 1.0499999523162842, 1.0199999809265137, 0.9900000095367432, 0.9700000286102295, 0.9599999785423279, 0.8600000143051147]; explained fractions [0.1850000023841858, 0.15600000321865082, 0.14800000190734863, 0.13899999856948853, 0.13500000536441803, 0.13099999725818634, 0.10499999672174454] (first component 0.19; isotropic would be 0.14 each).

| organism | RAW ∠ prompted-lie | RAW ∠ released org dim | RAW ∠ own fingerprint | shrink ∠ prompted | shrink ∠ released org dim | shrink ∠ released base dim | shrink ∠ own fingerprint | ‖fingerprint‖ | LW shrinkage |
|---|---|---|---|---|---|---|---|---|---|
| GS-F | 78.2° | 88.5° | 89.7° | 88.3° | 88.7° | 89.4° | 88.3° | 6.9 | 0.280 |
| GS-M | 87.7° | 87.0° | 88.4° | 86.8° | 89.9° | 89.5° | 87.4° | 6.9 | 0.203 |
| SB | 81.3° | 85.0° | 84.6° | 90.0° | 86.3° | 87.5° | 92.0° | 6.8 | 0.028 |
| AW | 79.2° | 86.5° | 80.1° | 88.8° | 86.6° | 86.4° | 88.8° | 8.0 | 0.009 |
| CO | 84.4° | 93.4° | 77.7° | 91.2° | 91.3° | 92.1° | 89.3° | 7.7 | 0.036 |
| HC | 82.2° | 88.1° | 89.7° | 88.8° | 88.1° | 86.6° | 87.7° | 6.0 | 0.021 |
| SP | 81.2° | 88.8° | 73.2° | 88.8° | 88.9° | 87.9° | 85.9° | 8.4 | 0.004 |

Fingerprint cosines (organism − base Alpaca mean), upper triangle: GS-F·GS-M +0.94, GS-F·SB +0.86, GS-F·AW +0.91, GS-F·CO +0.91, GS-F·HC +0.90, GS-F·SP +0.83, GS-M·SB +0.87, GS-M·AW +0.91, GS-M·CO +0.90, GS-M·HC +0.91, GS-M·SP +0.81, SB·AW +0.83, SB·CO +0.88, SB·HC +0.88, SB·SP +0.82, AW·CO +0.90, AW·HC +0.90, AW·SP +0.76, CO·HC +0.92, CO·SP +0.83, HC·SP +0.81

(prompted-lie vs released base dim: 83.9°)

## apollo pooling `mean`, layer 57

Cosine between organism directions (upper) / transfer AUROC i→j (row = trained on i):

| | GS-F | GS-M | SB | AW | CO | HC | SP |
|---|---|---|---|---|---|---|---|
| **GS-F** | 1 / 1.00 | +0.21 / 0.99 | -0.02 / 0.29 | +0.01 / 0.75 | +0.03 / 0.56 | +0.06 / 0.63 | +0.02 / 0.68 |
| **GS-M** | +0.21 / 1.00 | 1 / 1.00 | +0.00 / 0.51 | +0.01 / 0.41 | +0.02 / 0.79 | +0.04 / 0.60 | +0.01 / 0.53 |
| **SB** | -0.02 / 0.36 | +0.00 / 0.42 | 1 / 0.97 | -0.03 / 0.38 | +0.05 / 0.73 | -0.04 / 0.26 | -0.01 / 0.52 |
| **AW** | +0.01 / 0.65 | +0.01 / 0.52 | -0.03 / 0.53 | 1 / 0.95 | +0.01 / 0.38 | -0.05 / 0.39 | -0.12 / 0.42 |
| **CO** | +0.03 / 0.84 | +0.02 / 0.65 | +0.05 / 0.71 | +0.01 / 0.42 | 1 / 0.99 | -0.02 / 0.59 | -0.08 / 0.46 |
| **HC** | +0.06 / 0.77 | +0.04 / 0.65 | -0.04 / 0.66 | -0.05 / 0.41 | -0.02 / 0.32 | 1 / 0.98 | -0.04 / 0.53 |
| **SP** | +0.02 / 0.74 | +0.01 / 0.67 | -0.01 / 0.27 | -0.12 / 0.49 | -0.08 / 0.53 | -0.04 / 0.38 | 1 / 0.94 |

Raw diff-of-means cosines (upper) / common-whitened cosines (lower):

| | GS-F | GS-M | SB | AW | CO | HC | SP |
|---|---|---|---|---|---|---|---|
| **GS-F** | 1 | +0.82 | +0.06 | -0.01 | +0.00 | +0.11 | -0.02 |
| **GS-M** | +0.67 | 1 | -0.07 | -0.10 | -0.01 | +0.09 | -0.06 |
| **SB** | -0.00 | -0.02 | 1 | +0.33 | +0.24 | +0.07 | +0.16 |
| **AW** | +0.03 | +0.01 | -0.02 | 1 | +0.14 | -0.10 | +0.39 |
| **CO** | +0.01 | +0.00 | +0.02 | +0.01 | 1 | -0.12 | +0.18 |
| **HC** | +0.03 | +0.00 | -0.03 | +0.03 | -0.01 | 1 | -0.18 |
| **SP** | +0.04 | -0.01 | -0.02 | +0.06 | -0.01 | +0.07 | 1 |

Spearman(transfer AUROC, similarity) over 42 ordered pairs, 10 000 joint permutations: shrinkage-direction cosine ρ = 0.694 (p = 0.0008); raw diff-of-means cosine ρ = 0.177 (p = 0.3665); common-whitened cosine ρ = 0.339 (p = 0.1178).
SVD of the 7 unit directions: singular values [1.1100000143051147, 1.0700000524520874, 1.0299999713897705, 1.0, 0.9700000286102295, 0.9100000262260437, 0.8899999856948853]; explained fractions [0.1770000010728836, 0.164000004529953, 0.15199999511241913, 0.14399999380111694, 0.13300000131130219, 0.11800000071525574, 0.1120000034570694] (first component 0.18; isotropic would be 0.14 each).

| organism | RAW ∠ prompted-lie | RAW ∠ released org dim | RAW ∠ own fingerprint | shrink ∠ prompted | shrink ∠ released org dim | shrink ∠ released base dim | shrink ∠ own fingerprint | ‖fingerprint‖ | LW shrinkage |
|---|---|---|---|---|---|---|---|---|---|
| GS-F | 75.0° | 94.0° | 98.3° | 87.8° | 91.0° | 91.8° | 88.8° | 20.9 | 0.221 |
| GS-M | 88.3° | 91.8° | 96.5° | 87.4° | 89.2° | 88.7° | 88.7° | 21.2 | 0.142 |
| SB | 79.9° | 87.6° | 87.4° | 89.5° | 87.6° | 89.3° | 91.3° | 20.5 | 0.029 |
| AW | 87.5° | 90.0° | 72.7° | 90.2° | 89.1° | 87.3° | 89.5° | 26.1 | 0.012 |
| CO | 92.2° | 93.5° | 78.7° | 88.9° | 90.8° | 90.2° | 86.9° | 25.6 | 0.043 |
| HC | 86.0° | 88.7° | 94.7° | 86.6° | 86.1° | 86.2° | 90.7° | 18.6 | 0.026 |
| SP | 89.6° | 91.1° | 73.0° | 91.3° | 89.0° | 89.6° | 88.9° | 25.9 | 0.006 |

Fingerprint cosines (organism − base Alpaca mean), upper triangle: GS-F·GS-M +0.93, GS-F·SB +0.83, GS-F·AW +0.91, GS-F·CO +0.91, GS-F·HC +0.89, GS-F·SP +0.82, GS-M·SB +0.84, GS-M·AW +0.91, GS-M·CO +0.91, GS-M·HC +0.91, GS-M·SP +0.79, SB·AW +0.80, SB·CO +0.84, SB·HC +0.86, SB·SP +0.78, AW·CO +0.93, AW·HC +0.91, AW·SP +0.76, CO·HC +0.93, CO·SP +0.80, HC·SP +0.80

(prompted-lie vs released base dim: 86.7°)

## dyl pooling `pred`, layer 44

Cosine between organism directions (upper) / transfer AUROC i→j (row = trained on i):

| | GS-F | GS-M | SB | AW | CO | HC | SP |
|---|---|---|---|---|---|---|---|
| **GS-F** | 1 / 1.00 | +0.11 / 0.93 | +0.02 / 0.49 | +0.04 / 0.64 | -0.00 / 0.62 | +0.06 / 0.74 | +0.05 / 0.68 |
| **GS-M** | +0.11 / 0.99 | 1 / 0.98 | +0.01 / 0.49 | +0.05 / 0.54 | -0.04 / 0.72 | +0.08 / 0.69 | +0.04 / 0.68 |
| **SB** | +0.02 / 0.33 | +0.01 / 0.28 | 1 / 0.97 | +0.09 / 0.66 | +0.02 / 0.54 | +0.05 / 0.49 | -0.00 / 0.37 |
| **AW** | +0.04 / 0.37 | +0.05 / 0.18 | +0.09 / 0.59 | 1 / 0.93 | +0.06 / 0.43 | +0.15 / 0.50 | +0.07 / 0.51 |
| **CO** | -0.00 / 0.73 | -0.04 / 0.62 | +0.02 / 0.56 | +0.06 / 0.66 | 1 / 0.93 | +0.05 / 0.53 | -0.02 / 0.53 |
| **HC** | +0.06 / 0.98 | +0.08 / 0.85 | +0.05 / 0.48 | +0.15 / 0.71 | +0.05 / 0.67 | 1 / 0.92 | +0.06 / 0.63 |
| **SP** | +0.05 / 0.96 | +0.04 / 0.90 | -0.00 / 0.40 | +0.07 / 0.59 | -0.02 / 0.71 | +0.06 / 0.69 | 1 / 0.96 |

Raw diff-of-means cosines (upper) / common-whitened cosines (lower):

| | GS-F | GS-M | SB | AW | CO | HC | SP |
|---|---|---|---|---|---|---|---|
| **GS-F** | 1 | +0.81 | -0.02 | -0.26 | +0.43 | +0.59 | +0.44 |
| **GS-M** | +0.28 | 1 | -0.15 | -0.45 | +0.51 | +0.67 | +0.58 |
| **SB** | +0.02 | +0.01 | 1 | +0.31 | -0.17 | -0.28 | -0.42 |
| **AW** | +0.05 | -0.03 | +0.04 | 1 | -0.17 | -0.24 | -0.26 |
| **CO** | +0.04 | +0.01 | +0.07 | +0.03 | 1 | +0.64 | +0.67 |
| **HC** | +0.00 | -0.01 | +0.03 | +0.07 | -0.02 | 1 | +0.74 |
| **SP** | +0.03 | +0.05 | +0.02 | +0.02 | +0.04 | +0.05 | 1 |

Spearman(transfer AUROC, similarity) over 42 ordered pairs, 10 000 joint permutations: shrinkage-direction cosine ρ = 0.333 (p = 0.1496); raw diff-of-means cosine ρ = 0.684 (p = 0.0172); common-whitened cosine ρ = 0.211 (p = 0.2484).
SVD of the 7 unit directions: singular values [1.149999976158142, 1.0499999523162842, 0.9900000095367432, 0.9800000190734863, 0.9599999785423279, 0.9300000071525574, 0.9100000262260437]; explained fractions [0.1889999955892563, 0.15700000524520874, 0.14000000059604645, 0.13899999856948853, 0.13099999725818634, 0.12399999797344208, 0.11999999731779099] (first component 0.19; isotropic would be 0.14 each).

| organism | RAW ∠ prompted-lie | RAW ∠ released org dim | RAW ∠ own fingerprint | shrink ∠ prompted | shrink ∠ released org dim | shrink ∠ released base dim | shrink ∠ own fingerprint | ‖fingerprint‖ | LW shrinkage |
|---|---|---|---|---|---|---|---|---|---|
| GS-F | 66.3° | 74.6° | 96.0° | 89.4° | 83.1° | 83.2° | 89.4° | 35.6 | 0.076 |
| GS-M | 74.5° | 89.6° | 96.8° | 87.9° | 82.5° | 83.8° | 90.4° | 34.7 | 0.069 |
| SB | 90.3° | 107.3° | 100.2° | 90.7° | 89.3° | 92.8° | 88.9° | 51.4 | 0.094 |
| AW | 90.9° | 109.3° | 84.9° | 89.4° | 95.6° | 92.5° | 92.2° | 43.9 | 0.009 |
| CO | 78.8° | 34.5° | 69.3° | 89.5° | 86.9° | 93.5° | 92.9° | 47.1 | 0.013 |
| HC | 74.6° | 91.9° | 90.3° | 89.5° | 89.7° | 89.3° | 89.2° | 36.3 | 0.015 |
| SP | 77.7° | 62.8° | 92.9° | 89.9° | 89.5° | 88.8° | 87.8° | 40.6 | 0.060 |

Fingerprint cosines (organism − base Alpaca mean), upper triangle: GS-F·GS-M +0.91, GS-F·SB +0.46, GS-F·AW +0.88, GS-F·CO +0.69, GS-F·HC +0.87, GS-F·SP +0.89, GS-M·SB +0.52, GS-M·AW +0.89, GS-M·CO +0.73, GS-M·HC +0.88, GS-M·SP +0.89, SB·AW +0.61, SB·CO +0.88, SB·HC +0.60, SB·SP +0.58, AW·CO +0.81, AW·HC +0.92, AW·SP +0.92, CO·HC +0.80, CO·SP +0.79, HC·SP +0.91

(prompted-lie vs released base dim: 74.1°)


## Interpretation (added 2026-09-16 after v2)

- **apollo_L38**: SVD of the RAW unit directions — singular values [1.5, 1.35, 1.04, 0.85, 0.78, 0.58, 0.41], explained [0.322, 0.26, 0.155, 0.104, 0.086, 0.049, 0.024] (first component 0.32); common-whitened: first component 0.24; shrinkage: 0.19 (isotropic = 0.14). Spearman(transfer, similarity): raw ρ = 0.02 (p = 0.868), common-whitened ρ = 0.01 (p = 0.957), shrinkage ρ = 0.45 (p = 0.0266).
- **apollo_L57**: SVD of the RAW unit directions — singular values [1.39, 1.3, 1.03, 0.96, 0.83, 0.74, 0.41], explained [0.275, 0.242, 0.153, 0.13, 0.098, 0.078, 0.024] (first component 0.27); common-whitened: first component 0.24; shrinkage: 0.18 (isotropic = 0.14). Spearman(transfer, similarity): raw ρ = 0.18 (p = 0.366), common-whitened ρ = 0.34 (p = 0.118), shrinkage ρ = 0.69 (p = 0.0008).
- **dyl_L44**: SVD of the RAW unit directions — singular values [1.92, 1.07, 0.98, 0.72, 0.55, 0.48, 0.39], explained [0.528, 0.163, 0.138, 0.074, 0.044, 0.033, 0.022] (first component 0.53); common-whitened: first component 0.19; shrinkage: 0.19 (isotropic = 0.14). Spearman(transfer, similarity): raw ρ = 0.68 (p = 0.017), common-whitened ρ = 0.21 (p = 0.248), shrinkage ρ = 0.33 (p = 0.1496).

1. **Which metric to read.** With 150–190 rows per organism in 5120 dimensions, any direction that has been multiplied by an
   estimated inverse covariance (the shrinkage directions, and the common-whitened cosines) is dominated by the noise
   subspace: all such cosines are ≈ 0 except the gender pair, all such reference angles are ≈ 90°, and the shrinkage SVD is
   flat (first component 0.18–0.19 vs 0.14 isotropic). These are artefacts of n ≪ p, not evidence of orthogonality —
   the same directions transfer at AUROC 0.7–0.99 (M3). The RAW diff-of-means cosines are the interpretable geometry;
   the whitened metric should be revisited with a low-rank covariance (M5 resamples give 5× more rows).
2. **Raw structure (Apollo pooling, L38).** Gender pair cos 0.82; an AuditBench/sandbagger cluster (SB·AW 0.59, AW·SP 0.53,
   SB·CO 0.36, AW·CO 0.33, CO·SP 0.30, SB·SP 0.30); hallucinates_citations near-orthogonal to everything (≤ 0.12); gender
   vs the rest ≈ 0. First raw principal component carries ≈ 0.3 of the variance — a shared component plus organism-
   specific remainders, i.e. narrative C (graded) rather than A (one shared direction) or B (all separate).
3. **Raw structure (DYL pooling, L44).** Larger and signed: gender pair 0.81; CO·HC·SP triad 0.64–0.74; gender vs that
   triad 0.43–0.67; animal_welfare ANTI-aligned with the triad (−0.17 to −0.45) and sandbagger anti-aligned with the
   AuditBench organisms — consistent with AW's chance-level T4 and with the pre-answer state encoding something
   behaviour-specific (what is being denied) on top of a shared 'about to deny' component. Here the raw cosine DOES
   predict transfer (ρ = 0.68, p = 0.017); under the Apollo pooling it does not (ρ 0.03 / 0.18) — transfer there is
   carried by directions that a mean-difference cosine cannot see (cf. lr ≫ dim in M2/M3).
4. **Released probes vs organism directions.** Raw angles to the released organism dim checkpoints are 85–94° under
   the Apollo pooling (all organisms) — the instructed-pairs direction is essentially orthogonal to the organism's
   own auditing-set lie direction, which is why T0 is weak and CORAL-whitening (T1) or retraining (T3) helps. Under
   the DYL pooling the released directions are closer for the organisms where DYL works (CO 34°, SP 63°, GS-F 75°).
5. **Prompted-lie direction.** 75–92° from every organism direction (Apollo), 66–91° (DYL): trained-organism lies are
   not the prompted-lie direction in either pooling — matching Cooney's prompted→trained drop.
6. **Fine-tune fingerprint.** The organisms' Alpaca-mean shifts from base are mutually aligned (cos 0.80–0.94, one
   shared 'was fine-tuned' direction of norm 7–8 at L38, 21–26 at L57, 35–51 at L44/pred) and 73–98° from the lie
   directions: the fingerprint is not the lie signal (the fine-tune moved everything; the lie direction is elsewhere),
   with a mild alignment for the AuditBench organisms (SP 73°, AW 80°, CO 78° at L38).
Caveats: 19–25 lies per AuditBench organism; cosines between raw diff-of-means directions have sd ≈ 0.1 under
bootstrap (not computed here); a single layer per pooling.
