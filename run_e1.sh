#!/usr/bin/env bash
# E1: 2x2 control for the shared-map skew cost (논문개요 7.2, 실험과정및정의내역 8절).
#
#   per-key synchronized  syncLong  (counting(), long[])  syncAdder (LongAdder, UNORDERED only; no cells under the monitor)
#   no per-key lock       casAtomic (AtomicLong)            casAdder  (the LongAdder control)
# Not a strict 2x2 factorial (AstraReview2 R1): see run_review2.sh E1b for syncAtomic.
#
#   bash run_e1.sh               # about 15 minutes (estimate): step 1 + step 2
#   SKIP_N6=1 bash run_e1.sh     # step 1 only (N=1e5), about 7-8 minutes
#
# K=256 keeps the ConcurrentHashMap bin-head effect (결과분석표 11절) out of the way:
# the diagnostic found ~0% slow-path updates there for seed 20260929.
# Results go to results-e1/ only, so the paper figures (results/) are not affected.
set -euo pipefail
cd -- "$(dirname -- "$0")"

E1_DIR="${RESULTS_DIR:-results-e1}"

say() { printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
die() { printf '\nerror: %s\n' "$*"; exit 1; }

[[ "$(java -version 2>&1)" == *'"25.0.4.1"'* ]] || die "java is not Temurin 25.0.4.1"
if pids="$(pgrep -f 'org.openjdk.jmh.Main')"; then
    ps -o pid,stat,etime,command -p "$(echo "$pids" | paste -sd, -)" | cut -c1-120
    die "another JMH is running (STAT T = suspended by Ctrl+Z). Stop it first: fg then Ctrl+C, or kill <pid>"
fi
grep -q 'ControlBenchmark.casAtomic' build/classes/META-INF/BenchmarkList 2>/dev/null \
    || die "build has no ControlBenchmark. Run: bash build.sh"

say "check (correctness, includes the two E1 collectors)"
bash check.sh | tee /dev/stderr | grep '^PASS: 102 inputs' >/dev/null || die "correctness check failed"

export BENCH='research.skew.ControlBenchmark.*'
run_one() {  # label, expected rows, JMH args...
    local label="$1" expected="$2"; shift 2
    say "run: $label"
    RESULTS_DIR="$E1_DIR" bash run.sh full "$@"
    local dir rows
    dir="$(ls -dt "$E1_DIR"/full-* | head -1)"
    rows="$(( $(wc -l < "$dir/summary.csv") - 1 ))"
    [[ "$rows" == "$expected" ]] || die "$label: ${rows} rows in $dir/summary.csv (expected ${expected})"
    ! grep -qE '<failure>|Exception' "$dir/console.log" || die "$label: errors in $dir/console.log"
    grep -q 'common.parallelism=3' "$dir/console.log" || die "$label: pool parallelism setting missing"
    printf '  done: %s (%s rows)\n' "$dir" "$rows"
}

run_one "step 1: N=1e5, K=256, uniform/hot50/hot90" 12 \
    -p size=100000 -p cardinality=256 -p distribution=uniform,hot50,hot90 -p seed=20260929
if [[ "${SKIP_N6:-0}" == 1 ]]; then
    say "step 2 skipped (SKIP_N6=1)"
else
    run_one "step 2: N=1e6, K=256, uniform/hot50/hot90" 12 \
        -p size=1000000 -p cardinality=256 -p distribution=uniform,hot50,hot90 -p seed=20260929
fi

say "summary"
python3 - "$E1_DIR" <<'EOF' | tee "$E1_DIR/e1_summary.md"
import csv, glob, sys

root = sys.argv[1]
rows = {}
for path in sorted(glob.glob(f"{root}/full-*/summary.csv")):          # latest run wins
    for r in csv.DictReader(open(path, encoding="utf-8")):
        rows[(r["method"], int(r["size"]), int(r["cardinality"]), r["distribution"])] = (
            float(r["score_ms"]), float(r["error_ms"] or 0))

def fmt(v):
    return "-" if v is None else f"{v[0]:.3g} ± {v[1]:.2g}"

def rat(a, b):
    if a is None or b is None:
        return "-"
    overlap = a[0] - a[1] <= b[0] + b[1] and b[0] - b[1] <= a[0] + a[1]
    return f"×{a[0] / b[0]:.2f}" + (" (intervals overlap)" if overlap else "")

print("# E1: four downstream implementations (K=256, seed 20260929)\n")
print("ms ± JMH 99.9% interval (from all 15 measured iterations). Implementations:")
print("- syncLong  = counting() (long[]), per-key synchronized added by the JDK")
print("- syncAdder = LongAdder without CONCURRENT, per-key synchronized. The diagnostic found NO cells")
print("  under the monitor (diag/run_binhead.sh cells), so it is not a striped counter.")
print("- casAtomic = AtomicLong, CONCURRENT (no per-key synchronized)")
print("- casAdder  = LongAdder, CONCURRENT (the control)\n")
print("Ratios compare implementations; they are not independent cost shares (AstraReview2 R1, 7).\n")
for n in sorted({k[1] for k in rows}):
    print(f"## N={n:,}\n")
    print("| distribution | syncLong | syncAdder | casAtomic | casAdder | syncAdder ÷ casAdder | casAtomic ÷ casAdder | syncLong ÷ casAdder |")
    print("|---|---|---|---|---|---|---|---|")
    for d in ("uniform", "hot50", "hot90"):
        g = {m: rows.get((m, n, 256, d)) for m in ("syncLong", "syncAdder", "casAtomic", "casAdder")}
        print(f"| {d} | " + " | ".join(fmt(g[m]) for m in ("syncLong", "syncAdder", "casAtomic", "casAdder"))
              + f" | {rat(g['syncAdder'], g['casAdder'])} | {rat(g['casAtomic'], g['casAdder'])} | {rat(g['syncLong'], g['casAdder'])} |")
    print()
print("syncAdder ÷ casAdder: same LongAdder type, CONCURRENT removed (includes the adder's own adaptation).")
print("casAtomic ÷ casAdder: two concurrent counters without the per-key monitor.")
print("For a same-accumulator monitor comparison (syncAtomic vs casAtomic) see run_review2.sh step E1b.")
EOF
say "saved: $E1_DIR/e1_summary.md"
