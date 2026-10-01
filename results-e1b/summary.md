# E1b: same-counter monitor comparison (N=100,000, K=256, seed 20260929)

sync* = downstream without CONCURRENT (JDK adds per-key synchronized); cas* = CONCURRENT downstream.
syncAtomic and casAtomic use the identical AtomicLong accumulator; so do syncAdder and casAdder (LongAdder).
Under the per-key monitor the LongAdder did not create cells in the diagnostic (diag/run_binhead.sh cells).

| distribution | `syncLong` | `syncAtomic` | `casAtomic` | `syncAdder` | `casAdder` |
|---|---|---|---|---|---|
| uniform | 1.14 ± 0.066 | 1.15 ± 0.059 | 0.836 ± 0.01 | 1.17 ± 0.016 | 0.752 ± 0.0059 |
| hot50 | 4.46 ± 0.085 | 4.19 ± 0.055 | 1.58 ± 0.01 | 4.74 ± 0.26 | 0.546 ± 0.017 |
| hot90 | 7.84 ± 0.33 | 3.97 ± 0.42 | 2.29 ± 0.03 | 4.3 ± 0.55 | 0.345 ± 0.021 |

| comparison (ratio of times) | what changes | uniform | hot50 | hot90 |
|---|---|---|---|---|
| `syncAtomic` ÷ `casAtomic` | per-key monitor, same AtomicLong | ×1.37 | ×2.66 | ×1.74 |
| `syncAdder` ÷ `casAdder` | per-key monitor, same LongAdder type (cells differ, see diag) | ×1.56 | ×8.68 | ×12.47 |
| `casAtomic` ÷ `casAdder` | counter implementation, no monitor | ×1.11 | ×2.89 | ×6.62 |
| `syncAtomic` ÷ `syncAdder` | counter implementation, with monitor | ×0.98 (intervals overlap) | ×0.88 | ×0.92 (intervals overlap) |
| `syncLong` ÷ `syncAtomic` | long[] vs AtomicLong accumulator, with monitor | ×0.99 (intervals overlap) | ×1.06 | ×1.97 |

Fork means (hot90): syncLong 8.13 / 7.64 / 7.75; syncAtomic 4.2 / 3.46 / 4.26; casAtomic 2.25 / 2.3 / 2.31; syncAdder 5.01 / 3.98 / 3.92; casAdder 0.371 / 0.328 / 0.336

These are ratios between implementations, not independent cost shares.
