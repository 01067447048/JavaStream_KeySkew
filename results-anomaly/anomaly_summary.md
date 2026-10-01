# LongAdder control outlier check (hot90)

ms ± 99.9% CI half-width; (×r) = time / fastest K of the same N and seed in the same result set; ⚠ = r ≥ 2.

## Step 1: three input orders (seeds)

| N | K | paper run (seed 29) | seed 20260929 | seed 20260930 | seed 20261001 |
|---|---|---|---|---|---|
| 100,000 | 1024 | 2.05 ± 0.46 (×5.8) ⚠ | 2 ± 0.27 (×4.7) ⚠ | 0.362 ± 0.019 (×1.0) | 0.351 ± 0.0055 (×1.0) |
| 100,000 | 2048 | 2.6 ± 0.24 (×7.4) ⚠ | 2.44 ± 0.32 (×5.7) ⚠ | 0.395 ± 0.019 (×1.1) | 0.39 ± 0.0024 (×1.1) |
| 100,000 | 4096 | 0.433 ± 0.0025 (×1.2) | 0.428 ± 0.014 (×1.0) | 0.409 ± 0.015 (×1.1) | 0.416 ± 0.024 (×1.2) |
| 1,000,000 | 32768 | 4.05 ± 0.23 (×1.1) | 3.68 ± 0.026 (×1.0) | 3.58 ± 0.14 (×1.0) | 3.99 ± 0.28 (×1.0) |
| 1,000,000 | 65536 | 38 ± 5.3 (×10.3) ⚠ | 31.1 ± 3.9 (×8.5) ⚠ | 11.2 ± 2.7 (×3.1) ⚠ | 5.66 ± 0.25 (×1.4) |

## Step 2: 128-byte object alignment (seed 20260929)

| N | K | normal alignment (step 1, seed 29) | 128-byte alignment |
|---|---|---|---|
| 100,000 | 1024 | 2 ± 0.27 (×4.7) ⚠ | 2.13 ± 0.22 (×4.0) ⚠ |
| 100,000 | 2048 | 2.44 ± 0.32 (×5.7) ⚠ | 1.28 ± 0.1 (×2.4) ⚠ |
| 100,000 | 4096 | 0.428 ± 0.014 (×1.0) | 0.53 ± 0.026 (×1.0) |

## Automatic reading (heuristic, check the tables)

- Step 1 outliers (≥2× reference): [(100000, 1024, 20260929), (100000, 2048, 20260929), (1000000, 65536, 20260929), (1000000, 65536, 20260930)]
  - flagged K differ by seed (or vanish) -> outliers follow input order / layout
- Step 2 outliers with 128-byte alignment: [(100000, 1024, 20260929), (100000, 2048, 20260929)]
  - still present with alignment -> not explained by cache-line sharing

See 결과분석표.md 9.4 and the decision table in the chat/notes before concluding.
