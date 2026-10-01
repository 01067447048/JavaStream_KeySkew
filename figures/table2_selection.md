| size | cardinality | distribution | seed | fastest | fastest_ms | runner_up | runner_up_ms | speedup_vs_runner_up | verdict | fastest_stock |
|---|---|---|---|---|---|---|---|---|---|---|
| 100000 | 64 | uniform | 20260929 | parallelMerge | 0.1599 | sequential | 0.5119 | 3.20 | parallelMerge | parallelMerge |
| 100000 | 64 | hot50 | 20260929 | parallelMerge | 0.1672 | parallelConcurrentAdder | 0.4843 | 2.90 | parallelMerge | parallelMerge |
| 100000 | 64 | hot90 | 20260929 | parallelMerge | 0.1672 | parallelConcurrentAdder | 0.3509 | 2.10 | parallelMerge | parallelMerge |
| 10000 | 256 | uniform | 20260929 | parallelMerge | 0.0493 | sequential | 0.06365 | 1.29 | parallelMerge | parallelMerge |
| 10000 | 256 | hot50 | 20260929 | parallelMerge | 0.04718 | sequential | 0.0739 | 1.57 | parallelMerge | parallelMerge |
| 10000 | 256 | hot90 | 20260929 | parallelMerge | 0.04215 | parallelConcurrentAdder | 0.05663 | 1.34 | parallelMerge | parallelMerge |
| 100000 | 256 | uniform | 20260929 | parallelMerge | 0.1855 | sequential | 0.5127 | 2.76 | parallelMerge | parallelMerge |
| 100000 | 256 | hot50 | 20260929 | parallelMerge | 0.1918 | sequential | 0.5123 | 2.67 | parallelMerge | parallelMerge |
| 100000 | 256 | hot90 | 20260929 | parallelMerge | 0.1896 | parallelConcurrentAdder | 0.3525 | 1.86 | parallelMerge | parallelMerge |
| 1000000 | 256 | uniform | 20260929 | parallelMerge | 1.805 | sequential | 5.128 | 2.84 | parallelMerge | parallelMerge |
| 1000000 | 256 | hot50 | 20260929 | parallelMerge | 1.472 | parallelConcurrentAdder | 4.924 | 3.35 | parallelMerge | parallelMerge |
| 1000000 | 256 | hot90 | 20260929 | parallelMerge | 1.577 | parallelConcurrentAdder | 3.747 | 2.38 | parallelMerge | parallelMerge |
| 100000 | 1024 | uniform | 20260929 | parallelMerge | 0.2687 | sequential | 0.5435 | 2.02 | parallelMerge | parallelMerge |
| 100000 | 1024 | hot50 | 20260929 | parallelMerge | 0.2705 | sequential | 0.5351 | 1.98 | parallelMerge | parallelMerge |
| 100000 | 1024 | hot90 | 20260929 | parallelMerge | 0.257 | sequential | 0.5339 | 2.08 | parallelMerge | parallelMerge |
| 100000 | 2048 | uniform | 20260929 | parallelMerge | 0.4051 | sequential | 0.5999 | 1.48 | parallelMerge | parallelMerge |
| 100000 | 2048 | hot50 | 20260929 | parallelMerge | 0.399 | sequential | 0.5685 | 1.42 | parallelMerge | parallelMerge |
| 100000 | 2048 | hot90 | 20260929 | parallelMerge | 0.3062 | sequential | 0.563 | 1.84 | parallelMerge | parallelMerge |
| 100000 | 4096 | uniform | 20260929 | sequential | 0.6745 | parallelMerge | 0.6876 | 1.02 | tie (CI overlap) | sequential |
| 100000 | 4096 | hot50 | 20260929 | sequential | 0.6259 | parallelMerge | 0.6357 | 1.02 | tie (CI overlap) | sequential |
| 100000 | 4096 | hot90 | 20260929 | parallelMerge | 0.3597 | parallelConcurrentAdder | 0.4325 | 1.20 | parallelMerge | parallelMerge |
| 100000 | 8192 | uniform | 20260929 | sequential | 0.8671 | parallelMerge | 1.154 | 1.33 | sequential | sequential |
| 100000 | 8192 | hot50 | 20260929 | sequential | 0.8205 | parallelConcurrentAdder | 0.8422 | 1.03 | tie (CI overlap) | sequential |
| 100000 | 8192 | hot90 | 20260929 | parallelMerge | 0.4202 | parallelConcurrentAdder | 0.624 | 1.48 | parallelMerge | parallelMerge |
| 1000000 | 16384 | uniform | 20260929 | parallelMerge | 6.265 | sequential | 9.807 | 1.57 | parallelMerge | parallelMerge |
| 1000000 | 16384 | hot50 | 20260929 | parallelMerge | 6.416 | parallelConcurrentAdder | 6.808 | 1.06 | parallelMerge | parallelMerge |
| 1000000 | 16384 | hot90 | 20260929 | parallelConcurrentAdder | 3.677 | parallelMerge | 4.003 | 1.09 | parallelConcurrentAdder | parallelMerge |
| 1000000 | 32768 | uniform | 20260929 | parallelConcurrentAdder | 8.475 | parallelConcurrent | 9.783 | 1.15 | parallelConcurrentAdder | parallelConcurrent |
| 1000000 | 32768 | hot50 | 20260929 | parallelConcurrentAdder | 6.638 | sequential | 9.846 | 1.48 | parallelConcurrentAdder | sequential |
| 1000000 | 32768 | hot90 | 20260929 | parallelConcurrentAdder | 4.046 | parallelMerge | 4.787 | 1.18 | parallelConcurrentAdder | parallelMerge |
| 1000000 | 65536 | uniform | 20260929 | parallelConcurrentAdder | 8.284 | parallelConcurrent | 9.013 | 1.09 | parallelConcurrentAdder | parallelConcurrent |
| 1000000 | 65536 | hot50 | 20260929 | parallelConcurrentAdder | 6.863 | sequential | 12.24 | 1.78 | parallelConcurrentAdder | sequential |
| 1000000 | 65536 | hot90 | 20260929 | parallelMerge | 6.465 | sequential | 9.362 | 1.45 | parallelMerge | parallelMerge |
| 100000 | 256 | uniform | 20260930 | parallelMerge | 0.1841 | sequential | 0.5188 | 2.82 | parallelMerge | parallelMerge |
| 100000 | 256 | hot50 | 20260930 | parallelMerge | 0.1868 | sequential | 0.5168 | 2.77 | parallelMerge | parallelMerge |
| 100000 | 256 | hot90 | 20260930 | parallelMerge | 0.1963 | sequential | 0.5179 | 2.64 | parallelMerge | parallelMerge |
