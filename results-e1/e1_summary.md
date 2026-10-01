# E1: four downstream implementations (K=256, seed 20260929)

ms ± JMH 99.9% interval (from all 15 measured iterations). Implementations:
- syncLong  = counting() (long[]), per-key synchronized added by the JDK
- syncAdder = LongAdder without CONCURRENT, per-key synchronized. The diagnostic found NO cells
  under the monitor (diag/run_binhead.sh cells), so it is not a striped counter.
- casAtomic = AtomicLong, CONCURRENT (no per-key synchronized)
- casAdder  = LongAdder, CONCURRENT (the control)

Ratios compare implementations; they are not independent cost shares (AstraReview2 R1, 7).

## N=100,000

| distribution | syncLong | syncAdder | casAtomic | casAdder | syncAdder ÷ casAdder | casAtomic ÷ casAdder | syncLong ÷ casAdder |
|---|---|---|---|---|---|---|---|
| uniform | 1.07 ± 0.0059 | 1.15 ± 0.0059 | 0.839 ± 0.0037 | 0.742 ± 0.012 | ×1.55 | ×1.13 | ×1.45 |
| hot50 | 4.43 ± 0.041 | 4.44 ± 0.0094 | 1.58 ± 0.0098 | 0.541 ± 0.017 | ×8.20 | ×2.92 | ×8.19 |
| hot90 | 7.45 ± 0.6 | 3.77 ± 0.15 | 2.28 ± 0.029 | 0.335 ± 0.0061 | ×11.26 | ×6.82 | ×22.24 |

## N=1,000,000

| distribution | syncLong | syncAdder | casAtomic | casAdder | syncAdder ÷ casAdder | casAtomic ÷ casAdder | syncLong ÷ casAdder |
|---|---|---|---|---|---|---|---|
| uniform | 12.3 ± 0.17 | 12.8 ± 0.19 | 8.32 ± 0.14 | 6.66 ± 0.14 | ×1.92 | ×1.25 | ×1.85 |
| hot50 | 44.7 ± 0.73 | 45 ± 0.94 | 15.8 ± 0.15 | 5.32 ± 0.22 | ×8.44 | ×2.97 | ×8.39 |
| hot90 | 87.7 ± 11 | 44.8 ± 2 | 22.8 ± 0.2 | 4 ± 0.45 | ×11.21 | ×5.71 | ×21.95 |

syncAdder ÷ casAdder: same LongAdder type, CONCURRENT removed (includes the adder's own adaptation).
casAtomic ÷ casAdder: two concurrent counters without the per-key monitor.
For a same-accumulator monitor comparison (syncAtomic vs casAtomic) see run_review2.sh step E1b.
