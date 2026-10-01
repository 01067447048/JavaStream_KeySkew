#!/usr/bin/env bash
# Tests whether the LongAdder-control outliers (hot90: N=1e5 K=1024/2048, N=1e6 K=65536)
# come from false sharing. See 결과분석표.md 9.4.
#
#   bash run_anomaly.sh          # about 12-15 minutes (estimate)
#
# Step 1 (results-anomaly/):          same conditions with three seeds.
#   False sharing depends on which keys end up next to each other in memory, which
#   the input order decides -> outliers should move or vanish with other seeds.
# Step 2 (results-anomaly-align128/): -XX:ObjectAlignmentInBytes=128, so no two
#   objects can share a 128-byte cache line -> outliers should vanish.
# Results never go to results/, so the paper figures are not affected.
set -euo pipefail
cd -- "$(dirname -- "$0")"

STEP1_DIR="results-anomaly"
STEP2_DIR="results-anomaly-align128"
BASE_JVM="-Xms512m -Xmx512m -Djava.util.concurrent.ForkJoinPool.common.parallelism=3"
export BENCH='.*parallelConcurrentAdder'

say() { printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
die() { printf '\nerror: %s\n' "$*"; exit 1; }

[[ "$(java -version 2>&1)" == *'"25.0.4.1"'* ]] || die "java is not Temurin 25.0.4.1"
if pids="$(pgrep -f 'org.openjdk.jmh.Main')"; then
    ps -o pid,stat,etime,command -p "$(echo "$pids" | paste -sd, -)" | cut -c1-120
    die "another JMH is running (STAT T = suspended by Ctrl+Z). Stop it first: fg then Ctrl+C, or kill <pid>"
fi
grep -q 'parallelConcurrentAdder' build/classes/META-INF/BenchmarkList 2>/dev/null \
    || die "build has no parallelConcurrentAdder. Run: bash build.sh"

run_one() {  # results dir, label, expected rows, JMH args...
    local root="$1" label="$2" expected="$3"; shift 3
    say "run: $label"
    RESULTS_DIR="$root" bash run.sh full "$@"
    local dir rows
    dir="$(ls -dt "$root"/full-* | head -1)"
    rows="$(( $(wc -l < "$dir/summary.csv") - 1 ))"
    [[ "$rows" == "$expected" ]] || die "$label: ${rows} rows in $dir/summary.csv (expected ${expected})"
    ! grep -qE '<failure>|Exception' "$dir/console.log" || die "$label: errors in $dir/console.log"
    printf '  done: %s (%s conditions)\n' "$dir" "$rows"
}

run_one "$STEP1_DIR" "step 1a: N=1e5, K=1024/2048/4096, hot90, 3 seeds" 9 \
    -p size=100000 -p cardinality=1024,2048,4096 -p distribution=hot90 \
    -p seed=20260929,20260930,20261001
run_one "$STEP1_DIR" "step 1b: N=1e6, K=32768/65536, hot90, 3 seeds" 6 \
    -p size=1000000 -p cardinality=32768,65536 -p distribution=hot90 \
    -p seed=20260929,20260930,20261001
run_one "$STEP2_DIR" "step 2: N=1e5, K=1024/2048/4096, hot90, 128-byte object alignment" 3 \
    -p size=100000 -p cardinality=1024,2048,4096 -p distribution=hot90 \
    -jvmArgsAppend "$BASE_JVM -XX:ObjectAlignmentInBytes=128"

step2_dir="$(ls -dt "$STEP2_DIR"/full-* | head -1)"
grep -q 'ObjectAlignmentInBytes=128' "$step2_dir/console.log" \
    || die "step 2 did not run with -XX:ObjectAlignmentInBytes=128 (check '# VM options' in $step2_dir/console.log)"
grep -q 'common.parallelism=3' "$step2_dir/console.log" \
    || die "step 2 lost the pool parallelism setting (check '# VM options' in $step2_dir/console.log)"

say "summary"
python3 - "$STEP1_DIR" "$STEP2_DIR" <<'EOF' | tee "$STEP1_DIR/anomaly_summary.md"
import csv, glob, sys

def load(root):
    rows = {}
    for path in sorted(glob.glob(f"{root}/full-*/summary.csv")):
        for r in csv.DictReader(open(path, encoding="utf-8")):
            if r["method"] == "parallelConcurrentAdder" and r["distribution"] == "hot90":
                rows[(int(r["size"]), int(r["cardinality"]), int(r["seed"]))] = r
    return rows

def fastest(rows, n, s):
    """Reference = fastest K measured for this N and seed in the same result set."""
    times = [float(r["score_ms"]) for (nn, _, ss), r in rows.items() if nn == n and ss == s]
    return min(times) if times else None

def cell(r, ref):
    if not r:
        return "-"
    ms, err = float(r["score_ms"]), float(r["error_ms"] or 0)
    ratio = ms / ref if ref else float("nan")
    flag = " ⚠" if ratio >= 2 else ""
    return f"{ms:.3g} ± {err:.2g} (×{ratio:.1f}){flag}"

step1, step2, paper = load(sys.argv[1]), load(sys.argv[2]), load("results")
seeds = [20260929, 20260930, 20261001]

print("# LongAdder control outlier check (hot90)\n")
print("ms ± 99.9% CI half-width; (×r) = time / fastest K of the same N and seed "
      "in the same result set; ⚠ = r ≥ 2.\n")
print("## Step 1: three input orders (seeds)\n")
print("| N | K | paper run (seed 29) | " + " | ".join(f"seed {s}" for s in seeds) + " |")
print("|---|---|---|" + "---|" * len(seeds))
for n, ks in ((100000, [1024, 2048, 4096]), (1000000, [32768, 65536])):
    for k in ks:
        paper_cell = cell(paper.get((n, k, 20260929)), fastest(paper, n, 20260929))
        cells = [cell(step1.get((n, k, s)), fastest(step1, n, s)) for s in seeds]
        print(f"| {n:,} | {k} | {paper_cell} | " + " | ".join(cells) + " |")

print("\n## Step 2: 128-byte object alignment (seed 20260929)\n")
print("| N | K | normal alignment (step 1, seed 29) | 128-byte alignment |")
print("|---|---|---|---|")
for k in (1024, 2048, 4096):
    normal = cell(step1.get((100000, k, 20260929)), fastest(step1, 100000, 20260929))
    aligned = cell(step2.get((100000, k, 20260929)), fastest(step2, 100000, 20260929))
    print(f"| 100,000 | {k} | {normal} | {aligned} |")

def flagged(rows):
    return sorted((n, k, s) for (n, k, s), r in rows.items()
                  if float(r["score_ms"]) >= 2 * fastest(rows, n, s))

s1 = flagged(step1)
s2 = flagged(step2)
print("\n## Automatic reading (heuristic, check the tables)\n")
print(f"- Step 1 outliers (≥2× reference): {s1 or 'none'}")
by_seed = {s: {(n, k) for n, k, ss in s1 if ss == s} for s in seeds}
same_everywhere = all(by_seed[s] == by_seed[seeds[0]] for s in seeds) and bool(by_seed[seeds[0]])
print("  - same K flagged for every seed -> outliers follow K, not input order"
      if same_everywhere else
      "  - flagged K differ by seed (or vanish) -> outliers follow input order / layout")
print(f"- Step 2 outliers with 128-byte alignment: {s2 or 'none'}")
print("  - vanished with alignment -> consistent with false sharing"
      if not s2 else "  - still present with alignment -> not explained by cache-line sharing")
print("\nSee 결과분석표.md 9.4 and the decision table in the chat/notes before concluding.")
EOF
say "saved: $STEP1_DIR/anomaly_summary.md"
