# E2: stability re-measurement (long warmup: 2 s x 10, measure 2 s x 5, 5 forks)

Old = main run in results/ (1 s x 5 warmup, 1 s x 5, 3 forks). Trend = last / first measured iteration per fork.

## N=10,000, K=256, hot90

| method | old mean ± CI | old fork means | old trend | new mean ± CI | new fork means | new trend |
|---|---|---|---|---|---|---|
| sequential | 0.0706 ± 0.011 | 0.0711 / 0.0716 / 0.0691 | 0.67 / 0.68 / 1.01 | 0.0579 ± 0.0004 | 0.0578 / 0.0575 / 0.0584 / 0.0581 / 0.058 | 1.00 / 1.00 / 1.00 / 0.98 / 0.97 |
| parallelMerge | 0.0421 ± 0.0004 | 0.0421 / 0.0418 / 0.0426 | 1.00 / 0.99 / 1.00 | 0.0429 ± 0.0011 | 0.0416 / 0.0413 / 0.0441 / 0.0445 / 0.0428 | 0.99 / 1.00 / 1.01 / 1.00 / 0.99 |

sequential ÷ merge: old ×1.68, new ×1.35

## N=1,000,000, K=32768, uniform

| method | old mean ± CI | old fork means | old trend | new mean ± CI | new fork means | new trend |
|---|---|---|---|---|---|---|
| sequential | 11.9 ± 0.066 | 11.8 / 11.9 / 11.9 | 0.98 / 1.00 / 1.00 | 12 ± 0.11 | 11.8 / 12 / 11.8 / 12.1 / 12.2 | 1.00 / 0.98 / 1.00 / 1.00 / 1.00 |
| parallelMerge | 11.2 ± 0.55 | 11.6 / 11.6 / 10.5 | 1.01 / 1.01 / 1.00 | 11.1 ± 0.38 | 11.4 / 10.5 / 10.7 / 11.7 / 11.4 | 1.00 / 1.00 / 1.05 / 1.01 / 1.00 |
| parallelConcurrent | 9.78 ± 0.14 | 9.62 / 9.85 / 9.87 | 1.02 / 1.01 / 1.00 | 9.95 ± 0.25 | 10.3 / 9.97 / 9.93 / 9.48 / 10 | 1.01 / 1.00 / 1.00 / 0.99 / 1.00 |

sequential ÷ merge: old ×1.06, new ×1.08
- old ranking: parallelConcurrent < parallelMerge < sequential
- new ranking: parallelConcurrent < parallelMerge < sequential

A trend far from 1.00 means the fork had not settled during measurement.
