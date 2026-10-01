# E0: pre-sized ConcurrentHashMap (hot90, seed 20260929)

ms ± 99.9% CI half-width. ×r = default / presized (> 1: pre-sizing is faster).
Pre-sized map: new ConcurrentHashMap<>(4K) -> 8K bins, Key(0) alone in bin 0, no resize.

## Step 1: LongAdder control

| N | K | role | default | presized | default / presized |
|---|---|---|---|---|---|
| 10,000 | 256 | outlier in env B only | 0.0569 ± 0.0016 | 0.057 ± 0.0043 | ×1.00 (CI overlap) |
| 100,000 | 1024 | outlier | 2.42 ± 0.3 | 0.33 ± 0.039 | ×7.34 |
| 100,000 | 2048 | outlier | 2.83 ± 0.14 | 0.334 ± 0.018 | ×8.47 |
| 100,000 | 4096 | comparison | 0.428 ± 0.0027 | 0.42 ± 0.017 | ×1.02 (CI overlap) |
| 1,000,000 | 32768 | comparison | 3.74 ± 0.25 | 4.31 ± 0.21 | ×0.87 |
| 1,000,000 | 65536 | outlier | 32.7 ± 4.5 | 6.03 ± 0.17 | ×5.42 |

## Step 2: stock counting()

| N | K | role | default | presized | default / presized |
|---|---|---|---|---|---|
| 10,000 | 256 | outlier in env B only | 0.712 ± 0.024 | 0.674 ± 0.013 | ×1.06 |
| 100,000 | 1024 | outlier | 7.65 ± 0.45 | 8.25 ± 0.36 | ×0.93 (CI overlap) |
| 100,000 | 2048 | outlier | 7.67 ± 0.68 | 8.35 ± 0.48 | ×0.92 (CI overlap) |
| 100,000 | 4096 | comparison | 7.97 ± 0.45 | 8.34 ± 0.26 | ×0.96 (CI overlap) |
| 1,000,000 | 32768 | comparison | 96.7 ± 14 | 85.4 ± 10 | ×1.13 (CI overlap) |
| 1,000,000 | 65536 | outlier | 80.5 ± 15 | 90.3 ± 11 | ×0.89 (CI overlap) |

## Automatic reading (heuristic, check the tables)

- outlier conditions where pre-sizing is ≥2× faster (CIs apart): [(100000, 1024), (100000, 2048), (1000000, 65536)] of [(100000, 1024), (100000, 2048), (1000000, 65536)]
- comparison conditions where pre-sizing is ≥1.5× faster: none
  -> consistent with the bin-head mechanism: slowdowns vanish with pre-sizing, normal conditions barely move
- Step 2 (stock) is expected to change little: its per-key synchronized block already serializes the hot key.

See 결과분석표.md 11절 and 논문개요.md 7.2 before concluding.
