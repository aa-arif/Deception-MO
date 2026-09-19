# M5 / D20 — metrics under the three label sets (never mixed inside one evaluation set)

Label sets: **released** = the released graded labels; **judge** = claude-opus-4-8 (D19) on the same original transcripts; **+resamples** = originals plus the 4 resampled rollouts per question, judge labels (needs the resample features; '–' until then). lr AUROC [bootstrap CI]; T0 = released probes, T3 = leave-one-organism-out noleak, QD strict = question-disjoint LOO (AuditBench), T5 = same-organism 5-fold ceiling at its best layer (in-sample layer choice, as in M2).

## apollo pooling (mean over content tokens)

### n lie / honest and released probes (T0)

| organism | n — originals / released | n — originals / judge | n — originals+resamples / judge | T0 — originals / released | T0 — originals / judge | T0 — originals+resamples / judge |
|---|---|---|---|---|---|---|
| GS-F | 74/79 | 75/48 | 383/246 | 0.754 [0.67, 0.83] | 0.795 [0.71, 0.87] | 0.762 [0.71, 0.81] |
| GS-M | 51/79 | 57/72 | 293/355 | 0.839 [0.76, 0.91] | 0.829 [0.75, 0.90] | 0.836 [0.79, 0.87] |
| SB | 40/51 | 57/21 | 286/142 | 0.798 [0.70, 0.89] | 0.906 [0.83, 0.97] | 0.836 [0.78, 0.88] |
| AW | 25/145 | 39/111 | 210/557 | 0.820 [0.73, 0.90] | 0.767 [0.66, 0.85] | 0.798 [0.76, 0.84] |
| CO | 24/153 | 78/85 | 398/403 | 0.509 [0.36, 0.65] | 0.666 [0.58, 0.75] | 0.639 [0.59, 0.69] |
| HC | 19/143 | 25/145 | 165/697 | 0.668 [0.54, 0.81] | 0.684 [0.56, 0.82] | 0.723 [0.65, 0.79] |
| SP | 25/148 | 39/110 | 199/573 | 0.659 [0.53, 0.77] | 0.751 [0.65, 0.84] | 0.738 [0.67, 0.80] |

### transfer (T3 noleak lr) and question-disjoint strict LOO

| organism | T3 — originals / released | T3 — originals / judge | T3 — originals+resamples / judge | QDstrict — originals / released | QDstrict — originals / judge | QDstrict — originals+resamples / judge |
|---|---|---|---|---|---|---|
| GS-F | 0.976 [0.95, 1.00] | 1.000 [1.00, 1.00] | 1.000 [1.00, 1.00] | n/a | n/a | n/a |
| GS-M | 0.957 [0.92, 0.99] | 0.956 [0.91, 0.99] | 0.939 [0.92, 0.96] | n/a | n/a | n/a |
| SB | 0.821 [0.73, 0.90] | 0.981 [0.95, 1.00] | 0.952 [0.93, 0.97] | n/a | n/a | n/a |
| AW | 0.934 [0.89, 0.97] | 0.895 [0.84, 0.94] | 0.931 [0.90, 0.96] | 0.911 [0.84, 0.96] | 0.864 [0.79, 0.93] | 0.910 [0.87, 0.95] |
| CO | 0.931 [0.89, 0.97] | 0.904 [0.86, 0.95] | 0.900 [0.87, 0.93] | 0.930 [0.87, 0.97] | 0.912 [0.85, 0.96] | 0.887 [0.85, 0.92] |
| HC | 0.923 [0.85, 0.98] | 0.908 [0.85, 0.96] | 0.908 [0.87, 0.94] | 0.743 [0.61, 0.85] | 0.824 [0.73, 0.91] | 0.855 [0.81, 0.90] |
| SP | 0.909 [0.83, 0.96] | 0.894 [0.83, 0.95] | 0.914 [0.88, 0.94] | 0.916 [0.85, 0.98] | 0.845 [0.75, 0.92] | 0.901 [0.87, 0.93] |

### same-organism ceiling (T5 lr, best layer; dim in brackets)

| organism | T5 — originals / released | T5 — originals / judge | T5 — originals+resamples / judge | T5dim — originals / released | T5dim — originals / judge | T5dim — originals+resamples / judge |
|---|---|---|---|---|---|---|
| GS-F | 0.999 [1.00, 1.00] (L32) | 1.000 [1.00, 1.00] (L32) | 1.000 [1.00, 1.00] (L38) | 0.984 | 0.987 | 0.993 |
| GS-M | 0.994 [0.98, 1.00] (L57) | 0.963 [0.93, 0.99] (L38) | 0.968 [0.95, 0.98] (L57) | 0.872 | 0.798 | 0.853 |
| SB | 0.935 [0.87, 0.98] (L57) | 0.958 [0.92, 0.99] (L57) | 0.967 [0.94, 0.98] (L57) | 0.873 | 0.867 | 0.860 |
| AW | 0.895 [0.81, 0.97] (L57) | 0.846 [0.77, 0.92] (L57) | 0.917 [0.88, 0.94] (L57) | 0.725 | 0.712 | 0.717 |
| CO | 0.971 [0.93, 0.99] (L57) | 0.835 [0.77, 0.89] (L57) | 0.889 [0.86, 0.92] (L57) | 0.876 | 0.719 | 0.763 |
| HC | 0.987 [0.97, 1.00] (L57) | 0.861 [0.78, 0.93] (L57) | 0.936 [0.91, 0.96] (L57) | 0.801 | 0.570 | 0.846 |
| SP | 0.972 [0.95, 0.99] (L13) | 0.899 [0.83, 0.96] (L32) | 0.909 [0.87, 0.94] (L13) | 0.501 | 0.491 | 0.588 |

Medians over organisms — originals / released: T0 0.754, T3 0.931, T5 0.972; originals / judge: T0 0.767, T3 0.908, T5 0.899; originals+resamples / judge: T0 0.762, T3 0.931, T5 0.936

## dyl pooling (pre-answer state)

### n lie / honest and released probes (T0)

| organism | n — originals / released | n — originals / judge | n — originals+resamples / judge | T0 — originals / released | T0 — originals / judge | T0 — originals+resamples / judge |
|---|---|---|---|---|---|---|
| GS-F | 72/79 | 74/49 | – | 0.964 [0.92, 0.99] | 0.957 [0.90, 0.99] | – |
| GS-M | 51/78 | 58/73 | – | 0.888 [0.82, 0.94] | 0.842 [0.77, 0.91] | – |
| SB | 38/50 | 54/21 | – | 0.714 [0.59, 0.82] | 0.629 [0.47, 0.78] | – |
| AW | 22/136 | 35/105 | – | 0.624 [0.47, 0.78] | 0.630 [0.51, 0.75] | – |
| CO | 24/151 | 78/83 | – | 0.771 [0.67, 0.86] | 0.851 [0.79, 0.91] | – |
| HC | 15/130 | 22/133 | – | 0.523 [0.34, 0.71] | 0.670 [0.53, 0.82] | – |
| SP | 25/147 | 40/108 | – | 0.582 [0.44, 0.70] | 0.662 [0.55, 0.76] | – |

### transfer (T3 noleak lr) and question-disjoint strict LOO

| organism | T3 — originals / released | T3 — originals / judge | T3 — originals+resamples / judge | QDstrict — originals / released | QDstrict — originals / judge | QDstrict — originals+resamples / judge |
|---|---|---|---|---|---|---|
| GS-F | 0.975 [0.94, 1.00] | 0.997 [0.99, 1.00] | – | n/a | n/a | n/a |
| GS-M | 0.909 [0.86, 0.95] | 0.855 [0.79, 0.92] | – | n/a | n/a | n/a |
| SB | 0.787 [0.67, 0.88] | 0.838 [0.72, 0.93] | – | n/a | n/a | n/a |
| AW | 0.746 [0.63, 0.86] | 0.711 [0.62, 0.80] | – | 0.614 [0.48, 0.75] | 0.736 [0.63, 0.83] | – |
| CO | 0.768 [0.67, 0.86] | 0.840 [0.78, 0.90] | – | 0.774 [0.68, 0.87] | 0.842 [0.76, 0.91] | – |
| HC | 0.729 [0.58, 0.87] | 0.794 [0.67, 0.89] | – | 0.669 [0.51, 0.82] | 0.841 [0.75, 0.92] | – |
| SP | 0.741 [0.62, 0.85] | 0.847 [0.78, 0.91] | – | 0.675 [0.55, 0.80] | 0.783 [0.69, 0.87] | – |

### same-organism ceiling (T5 lr, best layer; dim in brackets)

| organism | T5 — originals / released | T5 — originals / judge | T5 — originals+resamples / judge | T5dim — originals / released | T5dim — originals / judge | T5dim — originals+resamples / judge |
|---|---|---|---|---|---|---|
| GS-F | 0.982 [0.95, 1.00] (L38) | 0.984 [0.95, 1.00] (L38) | – | 0.937 | 0.932 | – |
| GS-M | 0.932 [0.88, 0.97] (L38) | 0.815 [0.74, 0.88] (L38) | – | 0.873 | 0.765 | – |
| SB | 0.934 [0.88, 0.98] (L38) | 0.845 [0.73, 0.93] (L57) | – | 0.759 | 0.748 | – |
| AW | 0.849 [0.76, 0.92] (L38) | 0.738 [0.63, 0.83] (L38) | – | 0.531 | 0.531 | – |
| CO | 0.859 [0.77, 0.93] (L62) | 0.813 [0.74, 0.88] (L54) | – | 0.684 | 0.768 | – |
| HC | 0.877 [0.75, 0.97] (L38) | 0.777 [0.65, 0.89] (L54) | – | 0.569 | 0.669 | – |
| SP | 0.852 [0.76, 0.93] (L38) | 0.787 [0.68, 0.88] (L38) | – | 0.574 | 0.531 | – |

Medians over organisms — originals / released: T0 0.714, T3 0.768, T5 0.877; originals / judge: T0 0.670, T3 0.840, T5 0.813; originals+resamples / judge: T0 –, T3 –, T5 –

