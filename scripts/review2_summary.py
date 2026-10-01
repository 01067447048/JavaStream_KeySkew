#!/usr/bin/env python3
"""Markdown summaries for run_review2.sh (AstraReview2 extra experiments).

    python3 scripts/review2_summary.py E3  results-e3
    python3 scripts/review2_summary.py E1b results-e1b
    python3 scripts/review2_summary.py E2  results-e2

Latest run wins when the same row appears in several runs of one results folder.
Intervals are JMH 99.9% intervals, computed by JMH from all measured iterations
(forks x iterations), not from fork means. Overlap is not a test of equality.
"""
import csv
import glob
import statistics as st
import sys


def load(root):
    summary, raw = {}, {}
    for path in sorted(glob.glob(f"{root}/full-*/summary.csv")):
        for r in csv.DictReader(open(path, encoding="utf-8")):
            key = (r["method"], int(r["size"]), int(r["cardinality"]), r["distribution"],
                   int(r["seed"]), r.get("variant", ""))
            summary[key] = r
    for path in sorted(glob.glob(f"{root}/full-*/raw.csv")):
        rows = {}
        for r in csv.DictReader(open(path, encoding="utf-8")):
            if r["metric"] != "time":
                continue
            key = (r["method"], int(r["size"]), int(r["cardinality"]), r["distribution"],
                   int(r["seed"]), r.get("variant", ""))
            rows.setdefault(key, {}).setdefault(int(r["fork"]), []).append(float(r["value"]))
        raw.update(rows)
    return summary, raw


def cell(r):
    return "-" if r is None else f"{float(r['score_ms']):.3g} ± {float(r['error_ms'] or 0):.2g}"


def ratio(a, b):
    """a / b with a note when the two JMH intervals overlap."""
    if a is None or b is None:
        return "-"
    am, ae, bm, be = float(a["score_ms"]), float(a["error_ms"] or 0), float(b["score_ms"]), float(b["error_ms"] or 0)
    overlap = am - ae <= bm + be and bm - be <= am + ae
    return f"×{am / bm:.2f}" + (" (intervals overlap)" if overlap else "")


def forks(raw, key):
    f = raw.get(key)
    return "-" if not f else " / ".join(f"{st.mean(v):.3g}" for _, v in sorted(f.items()))


def trend(raw, key):
    """Per fork: last measured iteration / first measured iteration."""
    f = raw.get(key)
    return "-" if not f else " / ".join(f"{v[-1] / v[0]:.2f}" for _, v in sorted(f.items()))


def e3(root):
    s, raw = load(root)
    print("# E3: bin-head position on a fixed map (hot90, 2 keys in bin 0, no resize)\n")
    print("Map: new ConcurrentHashMap<>(16) -> 32 bins; hot Key(0) and cold Key(32) share bin 0.")
    print("head = [0, 32], second = [32, 0]. Layout and final counts were verified in every fork.\n")
    for n in sorted({k[1] for k in s}):
        g = {(m, p): s.get((m, n, 2, "hot90", 20260929, p)) for m in ("computeIfAbsent", "get") for p in ("head", "second")}
        print(f"## N={n:,}\n")
        print("| path | hot key first (head) | hot key second | second ÷ head | fork means head → second |")
        print("|---|---|---|---|---|")
        for m in ("computeIfAbsent", "get"):
            kh, ks = (m, n, 2, "hot90", 20260929, "head"), (m, n, 2, "hot90", 20260929, "second")
            print(f"| `{m}` | {cell(g[(m, 'head')])} | {cell(g[(m, 'second')])} | {ratio(g[(m, 'second')], g[(m, 'head')])} "
                  f"| {forks(raw, kh)} → {forks(raw, ks)} |")
        ch, cs = g[("computeIfAbsent", "head")], g[("computeIfAbsent", "second")]
        if ch and cs:
            hot = 0.9 * n
            print(f"\nPer hot-key record (time / 0.9N): computeIfAbsent head {float(ch['score_ms']) * 1e6 / hot:.1f} ns, "
                  f"second {float(cs['score_ms']) * 1e6 / hot:.1f} ns\n")
    print("## Reading\n")
    print("- If only `computeIfAbsent` slows down when the hot key is second, and `get` does not, the slowdown")
    print("  follows the first-node check of computeIfAbsent, with map size, keys, frequencies and resize held fixed.")
    print("- This is a mechanism microbenchmark on a pre-built map; do not mix its times with the aggregation results.")


def e1b(root):
    s, raw = load(root)
    methods = ("syncLong", "syncAtomic", "casAtomic", "syncAdder", "casAdder")
    print("# E1b: same-counter monitor comparison (N=100,000, K=256, seed 20260929)\n")
    print("sync* = downstream without CONCURRENT (JDK adds per-key synchronized); cas* = CONCURRENT downstream.")
    print("syncAtomic and casAtomic use the identical AtomicLong accumulator; so do syncAdder and casAdder (LongAdder).")
    print("Under the per-key monitor the LongAdder did not create cells in the diagnostic (diag/run_binhead.sh cells).\n")
    print("| distribution | " + " | ".join(f"`{m}`" for m in methods) + " |")
    print("|---|" + "---|" * len(methods))
    for d in ("uniform", "hot50", "hot90"):
        print(f"| {d} | " + " | ".join(cell(s.get((m, 100000, 256, d, 20260929, ""))) for m in methods) + " |")
    print("\n| comparison (ratio of times) | what changes | uniform | hot50 | hot90 |")
    print("|---|---|---|---|---|")
    pairs = [("syncAtomic", "casAtomic", "per-key monitor, same AtomicLong"),
             ("syncAdder", "casAdder", "per-key monitor, same LongAdder type (cells differ, see diag)"),
             ("casAtomic", "casAdder", "counter implementation, no monitor"),
             ("syncAtomic", "syncAdder", "counter implementation, with monitor"),
             ("syncLong", "syncAtomic", "long[] vs AtomicLong accumulator, with monitor")]
    for a, b, what in pairs:
        vals = [ratio(s.get((a, 100000, 256, d, 20260929, "")), s.get((b, 100000, 256, d, 20260929, "")))
                for d in ("uniform", "hot50", "hot90")]
        print(f"| `{a}` ÷ `{b}` | {what} | " + " | ".join(vals) + " |")
    print("\nFork means (hot90): " + "; ".join(
        f"{m} {forks(raw, (m, 100000, 256, 'hot90', 20260929, ''))}" for m in methods))
    print("\nThese are ratios between implementations, not independent cost shares.")


def e2(root):
    s, raw = load(root)
    old_s, old_raw = load("results")
    print("# E2: stability re-measurement (long warmup: 2 s x 10, measure 2 s x 5, 5 forks)\n")
    print("Old = main run in results/ (1 s x 5 warmup, 1 s x 5, 3 forks). Trend = last / first measured iteration per fork.\n")
    conds = [(10000, 256, "hot90", ("sequential", "parallelMerge")),
             (1000000, 32768, "uniform", ("sequential", "parallelMerge", "parallelConcurrent"))]
    for n, k, d, methods in conds:
        print(f"## N={n:,}, K={k}, {d}\n")
        print("| method | old mean ± CI | old fork means | old trend | new mean ± CI | new fork means | new trend |")
        print("|---|---|---|---|---|---|---|")
        for m in methods:
            key = (m, n, k, d, 20260929, "")
            print(f"| {m} | {cell(old_s.get(key))} | {forks(old_raw, key)} | {trend(old_raw, key)} "
                  f"| {cell(s.get(key))} | {forks(raw, key)} | {trend(raw, key)} |")
        seq, mer = ("sequential", n, k, d, 20260929, ""), ("parallelMerge", n, k, d, 20260929, "")
        print(f"\nsequential ÷ merge: old {ratio(old_s.get(seq), old_s.get(mer))}, new {ratio(s.get(seq), s.get(mer))}")
        if len(methods) == 3:
            for label, src in (("old", old_s), ("new", s)):
                rank = sorted(methods, key=lambda m: float(src[(m, n, k, d, 20260929, "")]["score_ms"])
                              if (m, n, k, d, 20260929, "") in src else 1e18)
                print(f"- {label} ranking: " + " < ".join(rank))
        print()
    print("A trend far from 1.00 means the fork had not settled during measurement.")


if __name__ == "__main__":
    {"E3": e3, "E1b": e1b, "E2": e2}[sys.argv[1]](sys.argv[2])
