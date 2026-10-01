# LongAdder cells of the hot key (Key 0), 5 parallel runs each, pool parallelism 3

| N | K | distribution | syncAdder cells per run | casAdder cells per run |
|---|---|---|---|---|
| 100,000 | 256 | uniform | 0/0/0/0/0 | 2/2/2/2/2 |
| 100,000 | 256 | hot50 | 0/0/0/0/0 | 8/8/8/8/16 |
| 100,000 | 256 | hot90 | 0/0/0/0/0 | 8/8/4/4/8 |
| 1,000,000 | 256 | uniform | 0/0/0/0/0 | 2/2/2/2/2 |
| 1,000,000 | 256 | hot50 | 0/0/0/0/0 | 16/16/16/8/16 |
| 1,000,000 | 256 | hot90 | 0/0/0/0/0 | 16/8/8/8/16 |
