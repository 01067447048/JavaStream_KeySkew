#!/usr/bin/env python3
"""Draw the paper figures and the selection table from results/*/summary.csv.

    .venv/bin/python scripts/plot_figures.py            # full-* runs only
    .venv/bin/python scripts/plot_figures.py --include-smoke   # layout check only

Outputs (figures/):
    fig1_scaling.pdf/.png        N vs time, uniform, K=256            (H1)
    fig2_skew.pdf/.png           distribution vs time, N=1e5 and 1e6  (H3, H4)
    fig3_cardinality.pdf/.png    K=64/256/8192 at N=1e5: time + alloc (H2)
    table2_selection.csv/.md     fastest method per condition, ties marked
    combined_summary.csv         every row the figures were drawn from

Error bars are the JMH 99.9% confidence interval (scoreConfidence).
If the same condition was measured in several runs, the latest run wins.
"""
import argparse
import csv
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
METHODS = ["sequential", "parallelMerge", "parallelConcurrent"]
LABELS = {
    "sequential": "Sequential (groupingBy)",
    "parallelMerge": "Parallel merge (groupingBy)",
    "parallelConcurrent": "Parallel concurrent (groupingByConcurrent)",
}
# Validated categorical slots 1-3 (all-pairs safe); marker + dash give a second,
# color-independent encoding for grayscale print.
STYLE = {
    "sequential": dict(color="#2a78d6", marker="o", linestyle="-"),
    "parallelMerge": dict(color="#eb6834", marker="s", linestyle="--"),
    "parallelConcurrent": dict(color="#1baf7a", marker="^", linestyle=":"),
}
DISTRIBUTIONS = ["uniform", "hot50", "hot90"]
DIST_LABELS = {"uniform": "Uniform", "hot50": "Hot 50%", "hot90": "Hot 90%"}
# Fig. 2 x axis: share of records on the hot key (uniform is about 1/K).
SHARE_LABELS = {"uniform": "Uniform", "hot50": "50%", "hot90": "90%"}
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


def fig2_skew(rows, out_dir):
    sizes = sorted({k[1] for k in rows if k[2] == BASE_K and k[4] == BASE_SEED})
    panels = [n for n in sizes if n >= 100_000] or sizes
    if not panels:
        print("skip fig2: no K=256 rows", file=sys.stderr)
        return
    fig, axes = plt.subplots(1, len(panels), figsize=(COLUMN_WIDTH, 2.6), squeeze=False)
    axes = axes[0]
    for ax, n in zip(axes, panels):
        for method in METHODS:
            pts = [(i, pick(rows, method, n, BASE_K, d)) for i, d in enumerate(DISTRIBUTIONS)]
            pts = [(i, p) for i, p in pts if p]
            if not pts:
                continue
            ax.errorbar([i for i, _ in pts], [p["score_ms"] for _, p in pts],
                        yerr=yerr([p for _, p in pts]), label=LABELS[method],
                        capsize=2, **STYLE[method])
        ax.set_xticks(range(len(DISTRIBUTIONS)))
        ax.set_xticklabels([SHARE_LABELS[d] for d in DISTRIBUTIONS])
        ax.set_xlim(-0.3, len(DISTRIBUTIONS) - 0.7)
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_formatter(ms_formatter())
        ax.set_title(f"N = $10^{{{len(str(n)) - 1}}}$", color=INK)
    axes[0].set_ylabel("Time per aggregation (ms)")
    fig.supxlabel("Hot-key share of records (K = 256)", fontsize=8, y=0.20)
    fig.subplots_adjust(bottom=0.40, wspace=0.35)
    legend_below(fig, axes[0])
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


def table2_selection(rows, out_dir):
    """Fastest method per condition; 'tie' when its CI overlaps the runner-up's."""
    conditions = sorted({k[1:] for k in rows},
                        key=lambda c: (c[3], c[1], c[0], DISTRIBUTIONS.index(c[2])
                                       if c[2] in DISTRIBUTIONS else 9))
    table = []
    for size, k, dist, seed in conditions:
        pts = sorted((p for m in METHODS if (p := rows.get((m, size, k, dist, seed)))),
                     key=lambda p: p["score_ms"])
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
    jmh_to_csv.write_csv(out_dir / "combined_summary.csv", fields,
                         [{f: r.get(f, "") for f in fields} for r in rows.values()])
    fig1_scaling(rows, out_dir)
    fig2_skew(rows, out_dir)
    fig3_cardinality(rows, out_dir)
    table2_selection(rows, out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
