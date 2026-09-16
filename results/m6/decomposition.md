# M6 — offset / rotation / novelty decomposition of each organism's lie direction

d = organism's raw diff-of-means lie direction on its auditing set. f = fine-tune fingerprint (organism − base Alpaca mean). B = base-lie
subspace (base prompted-lie direction from Varied Deception + released base dim probe). Fractions = share of ‖d‖² along f, along B (f removed),
and the residual (novel). AUROCs = the organism's lies vs honest scored along that component alone. Rotation = T1 CORAL gain (M4).

## apollo pooling `mean`, layer 38

| organism | ‖d‖ | frac along f (offset) | frac along B (base-lie) | frac novel | AUROC: f alone | AUROC: B-component | AUROC: novel component | AUROC: d | T1 raw → CORAL (rotation) | ∠(d, f) | ∠(d, prompted) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GS-F | 11.5 | 0.000 | 0.045 | 0.955 | 0.456 | 0.856 | 0.989 | 0.992 | 0.61 → 0.87 | 90° | 78° |
| GS-M | 9.3 | 0.001 | 0.002 | 0.998 | 0.547 | 0.586 | 0.931 | 0.934 | 0.50 → 0.67 | 88° | 88° |
| SB | 14.5 | 0.009 | 0.023 | 0.968 | 0.549 | 0.771 | 0.869 | 0.872 | 0.79 → 0.81 | 85° | 81° |
| AW | 12.2 | 0.029 | 0.036 | 0.934 | 0.610 | 0.752 | 0.785 | 0.763 | 0.78 → 0.81 | 80° | 79° |
| CO | 10.0 | 0.046 | 0.006 | 0.948 | 0.661 | 0.617 | 0.877 | 0.868 | 0.37 → 0.45 | 78° | 84° |
| HC | 8.9 | 0.000 | 0.020 | 0.980 | 0.485 | 0.675 | 0.888 | 0.877 | 0.75 → 0.84 | 90° | 82° |
| SP | 5.9 | 0.083 | 0.006 | 0.911 | 0.594 | 0.581 | 0.740 | 0.738 | 0.57 → 0.59 | 73° | 81° |

## dyl pooling `pred`, layer 44

| organism | ‖d‖ | frac along f (offset) | frac along B (base-lie) | frac novel | AUROC: f alone | AUROC: B-component | AUROC: novel component | AUROC: d | T1 raw → CORAL (rotation) | ∠(d, f) | ∠(d, prompted) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GS-F | 10.7 | 0.011 | 0.211 | 0.778 | 0.295 | 0.969 | 0.963 | 0.967 | 0.91 → 0.80 | 96° | 66° |
| GS-M | 13.9 | 0.014 | 0.122 | 0.864 | 0.332 | 0.895 | 0.877 | 0.881 | 0.72 → 0.60 | 97° | 74° |
| SB | 7.1 | 0.031 | 0.021 | 0.947 | 0.421 | 0.738 | 0.762 | 0.748 | 0.60 → 0.49 | 100° | 90° |
| AW | 5.5 | 0.008 | 0.003 | 0.990 | 0.515 | 0.518 | 0.713 | 0.707 | 0.53 → 0.54 | 85° | 91° |
| CO | 10.6 | 0.125 | 0.017 | 0.858 | 0.632 | 0.678 | 0.749 | 0.743 | 0.57 → 0.38 | 69° | 79° |
| HC | 7.8 | 0.000 | 0.097 | 0.903 | 0.482 | 0.655 | 0.692 | 0.691 | 0.44 → 0.57 | 90° | 75° |
| SP | 8.6 | 0.002 | 0.064 | 0.933 | 0.500 | 0.692 | 0.694 | 0.694 | 0.53 → 0.61 | 93° | 78° |

Reading: 'novel' is the part of the organism's lie direction outside the fingerprint and the base-lie subspace; its AUROC alone tells whether the
organism's lies are separable by something the base model's lie geometry does not contain. A large 'offset' fraction with AUROC(f) ≈ 0.5 means the
fingerprint direction is big but not discriminative (the fine-tune moved all activations, honest and lie alike).
