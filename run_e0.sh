#!/usr/bin/env bash
# E0: does a pre-sized ConcurrentHashMap remove the LongAdder-control slowdowns?
# Mechanism under test: 결과분석표 11절 (hot key behind another key in CHM bin 0).
#
#   bash run_e0.sh                     # about 15 minutes (estimate): step 1 + step 2
#   SKIP_STOCK=1 bash run_e0.sh        # step 1 only, about 7-8 minutes
#   RESULTS_DIR=results-e0-envB taskset -c 0-3 bash run_e0.sh   # environment B
#
# Step 1: adderDefault vs adderPresized       (the control, with and without pre-sizing)
# Step 2: concurrentDefault vs concurrentPresized (stock counting(); pre-sizing should not help much)
# Conditions: hot90, seed 20260929. Outlier conditions N=1e5 K=1024/2048, N=1e6 K=65536
# (N=1e4 K=256 in environment B); comparison conditions N=1e5 K=4096, N=1e6 K=32768.
# Results go to results-e0/ only, so the paper figures (results/) are not affected.
set -euo pipefail
cd -- "$(dirname -- "$0")"

E0_DIR="${RESULTS_DIR:-results-e0}"

say() { printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
die() { printf '\nerror: %s\n' "$*"; exit 1; }

[[ "$(java -version 2>&1)" == *'"25.0.4.1"'* ]] || die "java is not Temurin 25.0.4.1"
if pids="$(pgrep -f 'org.openjdk.jmh.Main')"; then
    ps -o pid,stat,etime,command -p "$(echo "$pids" | paste -sd, -)" | cut -c1-120
    die "another JMH is running (STAT T = suspended by Ctrl+Z). Stop it first: fg then Ctrl+C, or kill <pid>"
fi
grep -q 'PresizeBenchmark.adderPresized' build/classes/META-INF/BenchmarkList 2>/dev/null \
    || die "build has no PresizeBenchmark. Run: bash build.sh"

say "check (correctness, includes the two pre-sized collectors)"
bash check.sh | tee /dev/stderr | grep '^PASS: 102 inputs' >/dev/null || die "correctness check failed"

run_one() {  # label, expected rows, JMH args...
    local label="$1" expected="$2"; shift 2
    say "run: $label"
    RESULTS_DIR="$E0_DIR" bash run.sh full "$@"
    local dir rows
    dir="$(ls -dt "$E0_DIR"/full-* | head -1)"
    rows="$(( $(wc -l < "$dir/summary.csv") - 1 ))"
    [[ "$rows" == "$expected" ]] || die "$label: ${rows} rows in $dir/summary.csv (expected ${expected})"
    ! grep -qE '<failure>|Exception' "$dir/console.log" || die "$label: errors in $dir/console.log"
    grep -q 'common.parallelism=3' "$dir/console.log" || die "$label: pool parallelism setting missing"
    printf '  done: %s (%s rows)\n' "$dir" "$rows"
}

run_step() {  # step name, method regex
    local step="$1"
    export BENCH="research.skew.PresizeBenchmark.$2"
    run_one "$step: N=1e4, K=256"            2 -p size=10000   -p cardinality=256            -p distribution=hot90 -p seed=20260929
    run_one "$step: N=1e5, K=1024/2048/4096" 6 -p size=100000  -p cardinality=1024,2048,4096 -p distribution=hot90 -p seed=20260929
    run_one "$step: N=1e6, K=32768/65536"    4 -p size=1000000 -p cardinality=32768,65536    -p distribution=hot90 -p seed=20260929
}

run_step "step 1 (LongAdder control)" 'adder.*'
if [[ "${SKIP_STOCK:-0}" == 1 ]]; then
    say "step 2 skipped (SKIP_STOCK=1)"
else
    run_step "step 2 (stock counting)" 'concurrent.*'
fi

say "summary"
python3 - "$E0_DIR" <<'EOF' | tee "$E0_DIR/e0_summary.md"
import csv, glob, sys

root = sys.argv[1]
rows = {}
for path in sorted(glob.glob(f"{root}/full-*/summary.csv")):          # latest run wins
    for r in csv.DictReader(open(path, encoding="utf-8")):
        rows[(r["method"], int(r["size"]), int(r["cardinality"]))] = r

CONDS = [(10000, 256), (100000, 1024), (100000, 2048), (100000, 4096), (1000000, 32768), (1000000, 65536)]
OUTLIER = {(100000, 1024), (100000, 2048), (1000000, 65536)}   # both environments
ROLE = {c: "outlier" if c in OUTLIER else "comparison" for c in CONDS}
ROLE[(10000, 256)] = "outlier in env B only"

def get(m, n, k):
    r = rows.get((m, n, k))
    return None if r is None else (float(r["score_ms"]), float(r["error_ms"] or 0))

def fmt(v):
    return "-" if v is None else f"{v[0]:.3g} ± {v[1]:.2g}"

def ratio(a, b):
    if a is None or b is None:
        return "-", None
    overlap = a[0] - a[1] <= b[0] + b[1] and b[0] - b[1] <= a[0] + a[1]
    r = a[0] / b[0]
    return f"×{r:.2f}" + (" (CI overlap)" if overlap else ""), (r, overlap)

print("# E0: pre-sized ConcurrentHashMap (hot90, seed 20260929)\n")
print("ms ± 99.9% CI half-width. ×r = default / presized (> 1: pre-sizing is faster).")
print("Pre-sized map: new ConcurrentHashMap<>(4K) -> 8K bins, Key(0) alone in bin 0, no resize.\n")
reading = {}
for step, (dm, pm) in (("Step 1: LongAdder control", ("adderDefault", "adderPresized")),
                       ("Step 2: stock counting()", ("concurrentDefault", "concurrentPresized"))):
    if not any(k[0] == dm for k in rows):
        print(f"## {step}\n\nnot run\n")
        continue
    print(f"## {step}\n")
    print("| N | K | role | default | presized | default / presized |")
    print("|---|---|---|---|---|---|")
    for n, k in CONDS:
        d, p = get(dm, n, k), get(pm, n, k)
        text, val = ratio(d, p)
        reading[(dm, n, k)] = val
        print(f"| {n:,} | {k} | {ROLE[(n, k)]} | {fmt(d)} | {fmt(p)} | {text} |")
    print()

# Same-session reference: fastest adderPresized K per N shows whether outliers came back to normal.
print("## Automatic reading (heuristic, check the tables)\n")
if any((("adderDefault",) + c) in reading for c in CONDS):
    big = [c for c in OUTLIER if (v := reading.get(("adderDefault",) + c)) and v[0] >= 2 and not v[1]]
    small = [c for c in CONDS if c not in OUTLIER and c != (10000, 256)
             and (v := reading.get(("adderDefault",) + c)) and v[0] >= 1.5]
    print(f"- outlier conditions where pre-sizing is ≥2× faster (CIs apart): {sorted(big) or 'none'} of {sorted(OUTLIER)}")
    print(f"- comparison conditions where pre-sizing is ≥1.5× faster: {sorted(small) or 'none'}")
    if len(big) == len(OUTLIER) and not small:
        print("  -> consistent with the bin-head mechanism: slowdowns vanish with pre-sizing, normal conditions barely move")
    elif big:
        print("  -> partly consistent: some outliers vanish with pre-sizing")
    else:
        print("  -> not supported: check whether adderDefault reproduced the outliers in this session "
              "(the slowdown is bimodal per fork; compare with results/ and results-anomaly/)")
print("- Step 2 (stock) is expected to change little: its per-key synchronized block already serializes the hot key.")
print("\nSee 결과분석표.md 11절 and 논문개요.md 7.2 before concluding.")
EOF
say "saved: $E0_DIR/e0_summary.md"
