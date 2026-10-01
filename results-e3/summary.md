# E3: bin-head position on a fixed map (hot90, 2 keys in bin 0, no resize)

Map: new ConcurrentHashMap<>(16) -> 32 bins; hot Key(0) and cold Key(32) share bin 0.
head = [0, 32], second = [32, 0]. Layout and final counts were verified in every fork.

## N=100,000

| path | hot key first (head) | hot key second | second ÷ head | fork means head → second |
|---|---|---|---|---|
| `computeIfAbsent` | 0.796 ± 0.036 | 3.38 ± 0.1 | ×4.25 | 0.751 / 0.814 / 0.823 → 3.45 / 3.27 / 3.42 |
| `get` | 0.127 ± 0.0064 | 0.131 ± 0.0028 | ×1.03 (intervals overlap) | 0.123 / 0.132 / 0.125 → 0.129 / 0.13 / 0.134 |

Per hot-key record (time / 0.9N): computeIfAbsent head 8.8 ns, second 37.6 ns

## N=1,000,000

| path | hot key first (head) | hot key second | second ÷ head | fork means head → second |
|---|---|---|---|---|
| `computeIfAbsent` | 8.44 ± 0.52 | 56.9 ± 33 | ×6.74 | 8.1 / 8.29 / 8.92 → 32.9 / 38.7 / 99 |
| `get` | 1.35 ± 0.53 | 1.25 ± 0.032 | ×0.93 (intervals overlap) | 1.67 / 1.24 / 1.16 → 1.29 / 1.24 / 1.23 |

Per hot-key record (time / 0.9N): computeIfAbsent head 9.4 ns, second 63.2 ns

## Reading

- If only `computeIfAbsent` slows down when the hot key is second, and `get` does not, the slowdown
  follows the first-node check of computeIfAbsent, with map size, keys, frequencies and resize held fixed.
- This is a mechanism microbenchmark on a pre-built map; do not mix its times with the aggregation results.
