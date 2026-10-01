| size | cardinality | distribution | seed | fastest | fastest_ms | runner_up | runner_up_ms | speedup_vs_runner_up | verdict | fastest_stock |
|---|---|---|---|---|---|---|---|---|---|---|
| 100000 | 64 | uniform | 20260929 | parallelMerge | 0.4869 | parallelConcurrentAdder | 1.316 | 2.70 | parallelMerge | parallelMerge |
| 100000 | 64 | hot50 | 20260929 | parallelMerge | 0.5183 | parallelConcurrentAdder | 1.056 | 2.04 | parallelMerge | parallelMerge |
| 100000 | 64 | hot90 | 20260929 | parallelMerge | 0.5247 | parallelConcurrentAdder | 0.7093 | 1.35 | parallelMerge | parallelMerge |
| 10000 | 256 | uniform | 20260929 | parallelMerge | 0.1378 | sequential | 0.1543 | 1.12 | parallelMerge | parallelMerge |
| 10000 | 256 | hot50 | 20260929 | parallelMerge | 0.1363 | sequential | 0.1529 | 1.12 | parallelMerge | parallelMerge |
| 10000 | 256 | hot90 | 20260929 | parallelMerge | 0.1059 | sequential | 0.1527 | 1.44 | parallelMerge | parallelMerge |
| 100000 | 256 | uniform | 20260929 | parallelMerge | 0.566 | sequential | 1.406 | 2.48 | parallelMerge | parallelMerge |
| 100000 | 256 | hot50 | 20260929 | parallelMerge | 0.56 | sequential | 1.396 | 2.49 | parallelMerge | parallelMerge |
| 100000 | 256 | hot90 | 20260929 | parallelMerge | 0.6097 | parallelConcurrentAdder | 0.8899 | 1.46 | parallelMerge | parallelMerge |
| 1000000 | 256 | uniform | 20260929 | parallelMerge | 4.716 | sequential | 14.9 | 3.16 | parallelMerge | parallelMerge |
| 1000000 | 256 | hot50 | 20260929 | parallelMerge | 4.754 | parallelConcurrentAdder | 14.07 | 2.96 | parallelMerge | parallelMerge |
| 1000000 | 256 | hot90 | 20260929 | parallelMerge | 4.938 | parallelConcurrentAdder | 8.3 | 1.68 | parallelMerge | parallelMerge |
| 100000 | 1024 | uniform | 20260929 | parallelMerge | 0.951 | sequential | 1.588 | 1.67 | parallelMerge | parallelMerge |
| 100000 | 1024 | hot50 | 20260929 | parallelMerge | 0.9434 | sequential | 1.518 | 1.61 | parallelMerge | parallelMerge |
| 100000 | 1024 | hot90 | 20260929 | parallelMerge | 0.8666 | sequential | 1.56 | 1.80 | parallelMerge | parallelMerge |
| 100000 | 2048 | uniform | 20260929 | parallelMerge | 1.405 | sequential | 1.881 | 1.34 | parallelMerge | parallelMerge |
| 100000 | 2048 | hot50 | 20260929 | parallelMerge | 1.381 | parallelConcurrentAdder | 1.708 | 1.24 | parallelMerge | parallelMerge |
| 100000 | 2048 | hot90 | 20260929 | parallelMerge | 1.045 | sequential | 1.615 | 1.55 | parallelMerge | parallelMerge |
| 100000 | 4096 | uniform | 20260929 | parallelConcurrentAdder | 2.115 | parallelMerge | 2.227 | 1.05 | tie (CI overlap) | parallelMerge |
| 100000 | 4096 | hot50 | 20260929 | parallelConcurrentAdder | 1.676 | parallelMerge | 1.972 | 1.18 | parallelConcurrentAdder | parallelMerge |
| 100000 | 4096 | hot90 | 20260929 | parallelConcurrentAdder | 1.109 | parallelMerge | 1.222 | 1.10 | parallelConcurrentAdder | parallelMerge |
| 100000 | 8192 | uniform | 20260929 | parallelConcurrentAdder | 2.41 | parallelConcurrent | 2.606 | 1.08 | parallelConcurrentAdder | parallelConcurrent |
| 100000 | 8192 | hot50 | 20260929 | parallelConcurrentAdder | 1.903 | sequential | 2.421 | 1.27 | parallelConcurrentAdder | sequential |
| 100000 | 8192 | hot90 | 20260929 | parallelMerge | 1.363 | parallelConcurrentAdder | 1.732 | 1.27 | parallelMerge | parallelMerge |
| 1000000 | 16384 | uniform | 20260929 | parallelConcurrentAdder | 20.32 | parallelMerge | 22.32 | 1.10 | parallelConcurrentAdder | parallelMerge |
| 1000000 | 16384 | hot50 | 20260929 | parallelConcurrentAdder | 17.38 | parallelMerge | 19.64 | 1.13 | parallelConcurrentAdder | parallelMerge |
| 1000000 | 16384 | hot90 | 20260929 | parallelConcurrentAdder | 10.14 | parallelMerge | 11.97 | 1.18 | parallelConcurrentAdder | parallelMerge |
| 1000000 | 32768 | uniform | 20260929 | parallelConcurrentAdder | 23.79 | parallelConcurrent | 26.09 | 1.10 | parallelConcurrentAdder | parallelConcurrent |
| 1000000 | 32768 | hot50 | 20260929 | parallelConcurrentAdder | 19.72 | parallelMerge | 30.98 | 1.57 | parallelConcurrentAdder | parallelMerge |
| 1000000 | 32768 | hot90 | 20260929 | parallelConcurrentAdder | 12.25 | parallelMerge | 15.35 | 1.25 | parallelConcurrentAdder | parallelMerge |
| 1000000 | 65536 | uniform | 20260929 | parallelConcurrentAdder | 35.64 | parallelConcurrent | 36.9 | 1.04 | tie (CI overlap) | parallelConcurrent |
| 1000000 | 65536 | hot50 | 20260929 | parallelConcurrentAdder | 27.15 | sequential | 54.81 | 2.02 | parallelConcurrentAdder | sequential |
| 1000000 | 65536 | hot90 | 20260929 | parallelMerge | 22.68 | sequential | 29.93 | 1.32 | parallelMerge | parallelMerge |
| 100000 | 256 | uniform | 20260930 | parallelMerge | 0.571 | sequential | 1.463 | 2.56 | parallelMerge | parallelMerge |
| 100000 | 256 | hot50 | 20260930 | parallelMerge | 0.5661 | sequential | 1.393 | 2.46 | parallelMerge | parallelMerge |
| 100000 | 256 | hot90 | 20260930 | parallelMerge | 0.6103 | parallelConcurrentAdder | 0.8819 | 1.44 | parallelMerge | parallelMerge |
