#!/usr/bin/env python3
"""Draw the paper figures and the selection table from results/*/summary.csv.

    .venv/bin/python scripts/plot_figures.py            # full-* runs only
    .venv/bin/python scripts/plot_figures.py --include-smoke   # layout check only

Outputs (figures/):
    fig1_scaling.pdf/.png        N vs time, uniform, K=256            (H1)
    fig2_skew.pdf/.png           hot-key records vs time, log-log      (H3, F3)
    fig3_cardinality.pdf/.png    K=64/256/8192 at N=1e5: time + alloc (H2)
    fig4_boundary.pdf/.png       N/K vs sequential/merge time ratio, one line per N
    boundary.csv                 N/K where parallel merge stops beating sequential
    table2_selection.csv/.md     fastest method per condition, ties marked
    combined_summary.csv         every row the figures were drawn from

Error bars are the JMH 99.9% confidence interval (scoreConfidence).
If the same condition was measured in several runs, the latest run wins.
"""
import argparse
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jmh_to_csv  # noqa: E402

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter  # noqa: E402

BASE_SEED = 20260929
BASE_K = 256
# The three stock collectors (Fig. 1 and Fig. 3) ...
METHODS = ["sequential", "parallelMerge", "parallelConcurrent"]
# ... plus the lock-free control: groupingByConcurrent with a CONCURRENT
# LongAdder downstream (Fig. 2 and Table II).
ALL_METHODS = METHODS + ["parallelConcurrentAdder"]
LABELS = {
    "sequential": "Sequential (groupingBy)",
    "parallelMerge": "Parallel merge (groupingBy)",
    "parallelConcurrent": "Parallel concurrent (groupingByConcurrent)",
    "parallelConcurrentAdder": "Parallel concurrent + LongAdder downstream",
}
# Validated categorical slots 1-3 (all-pairs safe); marker + dash give a second,
# color-independent encoding for grayscale print.
STYLE = {
    "sequential": dict(color="#2a78d6", marker="o", linestyle="-"),
    "parallelMerge": dict(color="#eb6834", marker="s", linestyle="--"),
    "parallelConcurrent": dict(color="#1baf7a", marker="^", linestyle=":"),
    # Slot 4 is below 3:1 on white: always shown with a legend entry and marker.
    "parallelConcurrentAdder": dict(color="#eda100", marker="D", linestyle="-."),
}
# Fig. 4 lines are input sizes, not methods: grayscale ink + distinct markers.
SIZE_STYLE = [
    dict(color="#0b0b0b", marker="o", linestyle="-"),
    dict(color="#52514e", marker="s", linestyle="--"),
    dict(color="#9a9893", marker="D", linestyle=":"),
]
DISTRIBUTIONS = ["uniform", "hot50", "hot90"]
DIST_LABELS = {"uniform": "Uniform", "hot50": "Hot 50%", "hot90": "Hot 90%"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
COLUMN_WIDTH, DOUBLE_WIDTH = 3.5, 7.16  # IEEE inches

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 8,
    "axes.titlesize": 8,
    "axes.labelsize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "lines.linewidth": 1.2,
    "lines.markersize": 5,
    "pdf.fonttype": 42,  # embed TrueType fonts (IEEE PDF eXpress)
    "ps.fonttype": 42,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

NUMERIC = ["size", "cardinality", "seed", "score_ms", "ci_low_ms", "ci_high_ms",
           "alloc_bytes_per_op", "alloc_error_bytes_per_op"]


def load_rows(results_dir, include_smoke):
    """Latest run wins for each (method, size, K, distribution, seed)."""
    prefixes = ("full-", "smoke-") if include_smoke else ("full-",)
    rows = {}
    for run_dir in sorted(p for p in Path(results_dir).iterdir()
                          if p.is_dir() and p.name.startswith(prefixes)):
        summary = run_dir / "summary.csv"
        try:
            if summary.is_file():
                with open(summary, newline="", encoding="utf-8") as f:
                    run_rows = list(csv.DictReader(f))
            else:  # runs made before run.sh wrote CSV
                run_rows, _, _ = jmh_to_csv.convert(run_dir)
        except FileNotFoundError:
            print(f"skip {run_dir.name}: no jmh.json (failed run?)", file=sys.stderr)
            continue
        for row in run_rows:
            for key in NUMERIC:
                value = row.get(key, "")
                row[key] = float(value) if value not in ("", None) else None
            key = (row["method"], int(row["size"]), int(row["cardinality"]),
                   row["distribution"], int(row["seed"]))
            if key in rows:
                print(f"note: {key} in {rows[key]['run']} replaced by {row['run']}",
                      file=sys.stderr)
            rows[key] = row
    return rows


def pick(rows, method, size, k, dist, seed=BASE_SEED):
    return rows.get((method, size, k, dist, seed))


def yerr(points, low="ci_low_ms", high="ci_high_ms", value="score_ms"):
    """Asymmetric error bars; zero where JMH gave no interval (e.g. smoke runs)."""
    lower = [p[value] - p[low] if p[low] is not None else 0 for p in points]
    upper = [p[high] - p[value] if p[high] is not None else 0 for p in points]
    return [lower, upper]


def ms_formatter():
    return FuncFormatter(lambda v, _: f"{v:g}")


def log_ticks(axis):
    """Plain-number ticks at 1-2-5 steps on a log axis; no 6x10^-1 style labels."""
    axis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
    axis.set_major_formatter(ms_formatter())
    axis.set_minor_formatter(NullFormatter())


def save(fig, out_dir, name):
    for ext in ("pdf", "png"):
        fig.savefig(out_dir / f"{name}.{ext}")
    plt.close(fig)
    print(f"figure: {out_dir / name}.pdf/.png")


def legend_below(fig, axes):
    handles, labels = axes.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=1, frameon=False,
               bbox_to_anchor=(0.5, -0.02))


def fig1_scaling(rows, out_dir):
    sizes = sorted({k[1] for k in rows if k[2] == BASE_K and k[3] == "uniform"
                    and k[4] == BASE_SEED})
    if len(sizes) < 2:
        print("skip fig1: need uniform, K=256 at two or more N", file=sys.stderr)
        return
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 2.6))
    for method in METHODS:
        pts = [(n, pick(rows, method, n, BASE_K, "uniform")) for n in sizes]
        pts = [(n, p) for n, p in pts if p]
        if not pts:
            continue
        ax.errorbar([n for n, _ in pts], [p["score_ms"] for _, p in pts],
                    yerr=yerr([p for _, p in pts]), label=LABELS[method],
                    capsize=2, **STYLE[method])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(sizes)
    ax.set_xticklabels([f"$10^{{{len(str(n)) - 1}}}$" for n in sizes])
    ax.xaxis.set_minor_formatter(NullFormatter())
    log_ticks(ax.yaxis)
    ax.set_xlabel("Input size N (elements)")
    ax.set_ylabel("Time per aggregation (ms, log)")
    ax.set_title("Uniform keys, K = 256", color=INK)
    fig.subplots_adjust(bottom=0.36)
    legend_below(fig, ax)
    save(fig, out_dir, "fig1_scaling")


HOT_SHARE = {"hot50": 0.50, "hot90": 0.90}


def hot_records(size, k, dist):
    """Records on key 0, exactly as Workload.generate builds the input."""
    if dist in HOT_SHARE:
        return round(size * HOT_SHARE[dist])
    return size // k + (1 if size % k else 0)


def fig2_skew(rows, out_dir):
    """Time vs number of hot-key records (log-log), skewed inputs, K=256.

    Lines join the 50% and 90% points of one N. Uniform inputs are in Fig. 1.
    """
    sizes = sorted({k[1] for k in rows if k[2] == BASE_K and k[4] == BASE_SEED})
    if not sizes:
        print("skip fig2: no K=256 rows", file=sys.stderr)
        return
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 3.0))

    # Reference slope: median ns per hot-key record of the concurrent collector
    # over skewed inputs with N >= 1e5 (every K measured with the base seed).
    per_record = sorted(
        p["score_ms"] * 1e6 / hot_records(int(p["size"]), int(p["cardinality"]), p["distribution"])
        for (m, n, k, d, seed), p in rows.items()
        if m == "parallelConcurrent" and d in HOT_SHARE and n >= 100_000 and seed == BASE_SEED)

    for method in ALL_METHODS:
        for i, n in enumerate(sizes):
            pts = [(hot_records(n, BASE_K, d), pick(rows, method, n, BASE_K, d))
                   for d in HOT_SHARE]
            pts = [(x, p) for x, p in pts if p]
            if not pts:
                continue
            ax.errorbar([x for x, _ in pts], [p["score_ms"] for _, p in pts],
                        yerr=yerr([p for _, p in pts]),
                        label=LABELS[method] if i == 0 else None,
                        capsize=2, **STYLE[method])

    # Concurrent collector at other K: same line if the cost ignores K.
    extra = [(hot_records(n, k, d), p) for (m, n, k, d, seed), p in rows.items()
             if m == "parallelConcurrent" and k != BASE_K and d in HOT_SHARE
             and seed == BASE_SEED]
    other_ks = sorted({int(p["cardinality"]) for _, p in extra})
    if extra:
        style = STYLE["parallelConcurrent"]
        ax.plot([x for x, _ in extra], [p["score_ms"] for _, p in extra],
                linestyle="none", marker=style["marker"], markersize=7.5,
                markerfacecolor="none", markeredgecolor=style["color"],
                markeredgewidth=0.8, zorder=5,  # ring around the K=256 point it overlaps
                label="Parallel concurrent, K = " + (" / ".join(map(str, other_ks))
                    if len(other_ks) <= 2 else f"{other_ks[0]}–{other_ks[-1]} (K ≠ 256)"))

    if per_record:
        slope = per_record[len(per_record) // 2]
        xs = [min(hot_records(n, BASE_K, "hot50") for n in sizes) / 2,
              max(hot_records(n, BASE_K, "hot90") for n in sizes) * 1.5]
        ax.plot(xs, [x * slope / 1e6 for x in xs], color=MUTED, linewidth=0.8,
                linestyle=(0, (4, 2)), zorder=0,
                label=f"Reference: T = ({slope:.0f} ns) qN")

    # Direct labels at the right end of each flat sequential line.
    for n in sizes:
        p = pick(rows, "sequential", n, BASE_K, "hot90")
        if p:
            ax.annotate(f"N = $10^{{{len(str(n)) - 1}}}$",
                        (hot_records(n, BASE_K, "hot90"), p["score_ms"]),
                        textcoords="offset points", xytext=(6, -3), ha="left",
                        fontsize=6.5, color=MUTED)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(
        lambda v, _: f"$10^{{{int(round(math.log10(v)))}}}$"))
    ax.xaxis.set_minor_formatter(NullFormatter())
    log_ticks(ax.yaxis)
    ax.set_xlabel("Records on the hot key (log)")
    ax.set_ylabel("Time per aggregation (ms, log)")
    ax.set_xlim(right=max(hot_records(n, BASE_K, "hot90") for n in sizes) * 4)
    ax.set_title("Hot-key load and aggregation time (platform A)", color=INK)
    handles, labels = ax.get_legend_handles_labels()
    height = 2.2 + 0.16 * len(labels)  # grow the figure with the legend
    fig.set_size_inches(COLUMN_WIDTH, height)
    fig.subplots_adjust(bottom=(0.45 + 0.16 * len(labels)) / height)
    order = [LABELS[m] for m in ALL_METHODS] + [l for l in labels if l not in LABELS.values()]
    pairs = dict(zip(labels, handles))
    fig.legend([pairs[l] for l in order if l in pairs], [l for l in order if l in pairs],
               loc="lower center", ncol=1, frameon=False, bbox_to_anchor=(0.5, -0.02))
    save(fig, out_dir, "fig2_skew")


def fig3_cardinality(rows, out_dir, size=100_000):
    ks = sorted({k[2] for k in rows if k[1] == size and k[4] == BASE_SEED})
    if len(ks) < 2:
        print(f"skip fig3: need two or more K at N={size}", file=sys.stderr)
        return
    fig, axes = plt.subplots(2, len(DISTRIBUTIONS), figsize=(DOUBLE_WIDTH, 3.6),
                             sharex=True, sharey="row")
    for col, dist in enumerate(DISTRIBUTIONS):
        for method in METHODS:
            pts = [(k, pick(rows, method, size, k, dist)) for k in ks]
            pts = [(k, p) for k, p in pts if p]
            if not pts:
                continue
            xs = [k for k, _ in pts]
            axes[0][col].errorbar(xs, [p["score_ms"] for _, p in pts],
                                  yerr=yerr([p for _, p in pts]), label=LABELS[method],
                                  capsize=2, **STYLE[method])
            alloc = [p for _, p in pts if p["alloc_bytes_per_op"] is not None]
            if alloc:
                err = [p["alloc_error_bytes_per_op"] or 0 for p in alloc]
                axes[1][col].errorbar([int(p["cardinality"]) for p in alloc],
                                      [p["alloc_bytes_per_op"] / 1024 for p in alloc],
                                      yerr=[e / 1024 for e in err],
                                      capsize=2, **STYLE[method])
        axes[0][col].set_title(DIST_LABELS[dist], color=INK)
        for row in (0, 1):
            ax = axes[row][col]
            ax.set_xscale("log", base=2)
            ax.set_yscale("log")
            ax.set_xticks(ks)
            ax.set_xticklabels([str(k) for k in ks])
            ax.xaxis.set_minor_formatter(NullFormatter())
            log_ticks(ax.yaxis)
        axes[1][col].set_xlabel("Distinct keys K")
    axes[0][0].set_ylabel("Time (ms, log)")
    axes[1][0].set_ylabel("Allocation (KiB/op, log)")
    fig.suptitle(f"N = $10^{{{len(str(size)) - 1}}}$", fontsize=8, color=INK, y=0.99)
    fig.subplots_adjust(bottom=0.2, hspace=0.25, wspace=0.12)
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, -0.01))
    save(fig, out_dir, "fig3_cardinality")


def fig4_boundary(rows, out_dir):
    """Sequential / parallel-merge time ratio against N/K; > 1 means merge wins.

    If the crossover depends on N/K alone, the lines of different N cross 1 at
    the same N/K. boundary.csv holds the log-interpolated crossing per (N, dist).
    """
    series = {}
    for (m, n, k, d, seed), merge in rows.items():
        seq = rows.get(("sequential", n, k, d, seed))
        if m != "parallelMerge" or seed != BASE_SEED or not seq:
            continue
        ratio = seq["score_ms"] / merge["score_ms"]
        low = high = ratio
        if None not in (seq["ci_low_ms"], seq["ci_high_ms"], merge["ci_low_ms"], merge["ci_high_ms"]):
            low = seq["ci_low_ms"] / merge["ci_high_ms"]
            high = seq["ci_high_ms"] / merge["ci_low_ms"]
        series.setdefault((n, d), []).append((n / k, ratio, low, high, k))
    if not any(len(v) >= 2 for v in series.values()):
        print("skip fig4: need two or more K for some N", file=sys.stderr)
        return

    sizes = sorted({n for n, _ in series})
    fig, axes = plt.subplots(1, len(DISTRIBUTIONS), figsize=(DOUBLE_WIDTH, 2.4), sharey=True)
    crossings = []
    for ax, dist in zip(axes, DISTRIBUTIONS):
        ax.axhline(1.0, color=MUTED, linewidth=0.8, zorder=0)
        for i, n in enumerate(sizes):
            pts = sorted(series.get((n, dist), []))
            if not pts:
                continue
            ax.errorbar([p[0] for p in pts], [p[1] for p in pts],
                        yerr=[[p[1] - p[2] for p in pts], [p[3] - p[1] for p in pts]],
                        capsize=2, label=f"N = $10^{{{len(str(n)) - 1}}}$",
                        **SIZE_STYLE[i % len(SIZE_STYLE)])
            crossing = ""
            for (x0, r0, *_), (x1, r1, *_) in zip(pts, pts[1:]):
                if (r0 - 1) * (r1 - 1) < 0:  # log-log interpolation to ratio 1
                    t = math.log(r0) / (math.log(r0) - math.log(r1))
                    crossing = math.exp(math.log(x0) + t * (math.log(x1) - math.log(x0)))
            crossings.append({
                "size": n, "distribution": dist,
                "n_over_k": " ".join(f"{p[0]:.4g}" for p in pts),
                "ratio_seq_over_merge": " ".join(f"{p[1]:.3g}" for p in pts),
                "crossover_n_over_k": f"{crossing:.3g}" if crossing else
                ("single N/K" if len(pts) < 2
                 else "none (merge always faster)" if all(p[1] > 1 for p in pts)
                 else "none (sequential always faster)" if all(p[1] < 1 for p in pts)
                 else "multiple"),
            })
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.xaxis.set_major_formatter(ms_formatter())
        ax.xaxis.set_minor_formatter(NullFormatter())
        log_ticks(ax.yaxis)
        ax.set_title(DIST_LABELS[dist], color=INK)
        ax.set_xlabel("Records per key, N/K (log)")
    axes[0].set_ylabel("Sequential / parallel merge\n(> 1: merge faster, log)")
    axes[0].annotate("equal", (1, 1), xycoords=("axes fraction", "data"),
                     xytext=(-2, 3), textcoords="offset points", ha="right",
                     fontsize=6.5, color=MUTED)
    fig.subplots_adjust(bottom=0.32, wspace=0.08)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=len(labels), frameon=False,
               bbox_to_anchor=(0.5, -0.02))
    save(fig, out_dir, "fig4_boundary")
    jmh_to_csv.write_csv(out_dir / "boundary.csv", list(crossings[0]), crossings)
    print(f"table: {out_dir / 'boundary.csv'} ({len(crossings)} rows)")


def table2_selection(rows, out_dir):
    """Fastest method per condition; 'tie' when its CI overlaps the runner-up's."""
    conditions = sorted({k[1:] for k in rows},
                        key=lambda c: (c[3], c[1], c[0], DISTRIBUTIONS.index(c[2])
                                       if c[2] in DISTRIBUTIONS else 9))
    table = []
    for size, k, dist, seed in conditions:
        pts = sorted((p for m in ALL_METHODS if (p := rows.get((m, size, k, dist, seed)))),
                     key=lambda p: p["score_ms"])
        stock = [p for p in pts if p["method"] in METHODS]
        if len(pts) < 2:
            continue
        best, second = pts[0], pts[1]
        overlap = (best["ci_high_ms"] is None or second["ci_low_ms"] is None
                   or best["ci_high_ms"] >= second["ci_low_ms"])
        table.append({
            "size": size, "cardinality": k, "distribution": dist, "seed": seed,
            "fastest": best["method"],
            "fastest_ms": f"{best['score_ms']:.4g}",
            "runner_up": second["method"],
            "runner_up_ms": f"{second['score_ms']:.4g}",
            "speedup_vs_runner_up": f"{second['score_ms'] / best['score_ms']:.2f}",
            "verdict": "tie (CI overlap)" if overlap else best["method"],
            "fastest_stock": stock[0]["method"] if stock else "",
        })
    if not table:
        print("skip table2: no complete condition", file=sys.stderr)
        return
    fields = list(table[0])
    jmh_to_csv.write_csv(out_dir / "table2_selection.csv", fields, table)
    with open(out_dir / "table2_selection.md", "w", encoding="utf-8") as f:
        f.write("| " + " | ".join(fields) + " |\n")
        f.write("|" + "---|" * len(fields) + "\n")
        for row in table:
            f.write("| " + " | ".join(str(row[c]) for c in fields) + " |\n")
    print(f"table: {out_dir / 'table2_selection'}.csv/.md ({len(table)} conditions)")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", default="results")
    parser.add_argument("--out", default="figures")
    parser.add_argument("--include-smoke", action="store_true",
                        help="also read smoke-* runs (layout check only, not for the paper)")
    args = parser.parse_args()

    rows = load_rows(args.results, args.include_smoke)
    if not rows:
        print("No results found. Run: bash run.sh full", file=sys.stderr)
        return 1
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    fields = jmh_to_csv.SUMMARY_FIELDS
    as_int = {"size", "cardinality", "seed"}  # parsed as float in load_rows
    jmh_to_csv.write_csv(out_dir / "combined_summary.csv", fields,
                         [{f: int(r[f]) if f in as_int else r.get(f, "") for f in fields}
                          for r in rows.values()])
    fig1_scaling(rows, out_dir)
    fig2_skew(rows, out_dir)
    fig3_cardinality(rows, out_dir)
    fig4_boundary(rows, out_dir)
    table2_selection(rows, out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
