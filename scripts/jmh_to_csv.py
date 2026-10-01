#!/usr/bin/env python3
"""Convert one JMH result folder (jmh.json) into summary.csv and raw.csv.

Uses only the Python standard library, so run.sh can call it after every run.

    python3 scripts/jmh_to_csv.py results/full-20260930T010203Z.AbCdEf

summary.csv:   one row per (method, size, cardinality, distribution, seed).
raw.csv:       one row per measured iteration (fork x iteration), for time and allocation.
secondary.csv: every secondary metric JMH reported (gc.*, and perfnorm counters
               such as cycles or L1-dcache-load-misses when -prof perfnorm is used).
"""
import csv
import json
import math
import sys
from pathlib import Path

SUMMARY_FIELDS = [
    "run", "method", "size", "cardinality", "distribution", "seed", "variant",
    "score_ms", "error_ms", "ci_low_ms", "ci_high_ms", "samples",
    "elements_per_sec",
    "alloc_bytes_per_op", "alloc_error_bytes_per_op",
    "gc_count", "gc_time_ms",
    "forks", "warmup_iterations", "warmup_time",
    "measurement_iterations", "measurement_time", "threads",
    "pool_parallelism", "jvm_args", "jdk_version", "vm_version", "jmh_version",
]
SECONDARY_FIELDS = [
    "run", "method", "size", "cardinality", "distribution", "seed", "variant",
    "metric", "unit", "score", "error",
]
RAW_FIELDS = [
    "run", "method", "size", "cardinality", "distribution", "seed", "variant",
    "metric", "unit", "fork", "iteration", "value",
]
POOL_PROPERTY = "-Djava.util.concurrent.ForkJoinPool.common.parallelism="


def _num(value):
    """JMH writes 'NaN' as a string when there are too few samples; keep it blank."""
    if value is None or value == "NaN":
        return ""
    value = float(value)
    return "" if math.isnan(value) else value


def _pool_parallelism(jvm_args):
    for arg in jvm_args:
        if arg.startswith(POOL_PROPERTY):
            return arg[len(POOL_PROPERTY):]
    return ""


def convert(run_dir):
    """Return (summary_rows, raw_rows, secondary_rows) for run_dir/jmh.json."""
    run_dir = Path(run_dir)
    json_path = run_dir / "jmh.json"
    if not json_path.is_file() or json_path.stat().st_size == 0:
        raise FileNotFoundError(f"No JMH result: {json_path}")
    results = json.loads(json_path.read_text(encoding="utf-8"))

    summary, raw, extra = [], [], []
    for result in results:
        params = result.get("params", {})
        common = {
            "run": run_dir.name,
            "method": result["benchmark"].rsplit(".", 1)[-1],
            "size": int(params["size"]),
            "cardinality": int(params["cardinality"]),
            "distribution": params["distribution"],
            "seed": int(params["seed"]),
            # Extra benchmark parameter (BinHeadBenchmark: position); blank for the others.
            "variant": params.get("position", ""),
        }
        primary = result["primaryMetric"]
        if primary["scoreUnit"] != "ms/op":
            raise ValueError(f"Unexpected unit {primary['scoreUnit']} in {json_path}")
        low, high = primary["scoreConfidence"]
        secondary = result.get("secondaryMetrics", {})
        alloc = secondary.get("gc.alloc.rate.norm", {})
        score = _num(primary["score"])

        summary.append({
            **common,
            "score_ms": score,
            "error_ms": _num(primary["scoreError"]),
            "ci_low_ms": _num(low),
            "ci_high_ms": _num(high),
            "samples": sum(len(fork) for fork in primary.get("rawData", [])),
            "elements_per_sec": common["size"] * 1000.0 / score if score else "",
            "alloc_bytes_per_op": _num(alloc.get("score")),
            "alloc_error_bytes_per_op": _num(alloc.get("scoreError")),
            "gc_count": _num(secondary.get("gc.count", {}).get("score")),
            "gc_time_ms": _num(secondary.get("gc.time", {}).get("score")),
            "forks": result.get("forks", ""),
            "warmup_iterations": result.get("warmupIterations", ""),
            "warmup_time": result.get("warmupTime", ""),
            "measurement_iterations": result.get("measurementIterations", ""),
            "measurement_time": result.get("measurementTime", ""),
            "threads": result.get("threads", ""),
            "pool_parallelism": _pool_parallelism(result.get("jvmArgs", [])),
            "jvm_args": " ".join(result.get("jvmArgs", [])),
            "jdk_version": result.get("jdkVersion", ""),
            "vm_version": result.get("vmVersion", ""),
            "jmh_version": result.get("jmhVersion", ""),
        })

        for name, metric in sorted(secondary.items()):
            extra.append({**common, "metric": name, "unit": metric.get("scoreUnit", ""),
                          "score": _num(metric.get("score")),
                          "error": _num(metric.get("scoreError"))})

        for metric, unit, data in (
            ("time", "ms/op", primary.get("rawData", [])),
            ("alloc", "B/op", alloc.get("rawData", [])),
        ):
            for fork_index, fork in enumerate(data, start=1):
                for iteration, value in enumerate(fork, start=1):
                    raw.append({**common, "metric": metric, "unit": unit,
                                "fork": fork_index, "iteration": iteration,
                                "value": _num(value)})
    return summary, raw, extra


def write_csv(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main(argv):
    if len(argv) != 2:
        print("Usage: python3 scripts/jmh_to_csv.py results/<run-folder>", file=sys.stderr)
        return 2
    run_dir = Path(argv[1])
    summary, raw, extra = convert(run_dir)
    write_csv(run_dir / "summary.csv", SUMMARY_FIELDS, summary)
    write_csv(run_dir / "raw.csv", RAW_FIELDS, raw)
    write_csv(run_dir / "secondary.csv", SECONDARY_FIELDS, extra)
    print(f"CSV: {run_dir / 'summary.csv'} ({len(summary)} rows), "
          f"raw.csv ({len(raw)} rows), secondary.csv ({len(extra)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
