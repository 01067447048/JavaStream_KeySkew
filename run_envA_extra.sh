#!/usr/bin/env bash
# Environment A (macOS) extra runs for the generality experiments.
# Existing results/ are kept; these runs only add what is missing:
#   ② LongAdder control (parallelConcurrentAdder) for the conditions already measured
#   ① N/K boundary: new K values at N=1e5 and N=1e6, all four methods
#
#   bash run_envA_extra.sh     # about 45-55 minutes (estimate)
set -euo pipefail
cd -- "$(dirname -- "$0")"

say() { printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
die() { printf '\nerror: %s\n' "$*"; exit 1; }

run_one() {  # label, expected rows, then env/JMH args passed to run.sh
    local label="$1" expected="$2"; shift 2
    say "run: $label"
    "$@"
    local dir rows
    dir="$(ls -dt results/full-* | head -1)"
    rows="$(( $(wc -l < "$dir/summary.csv") - 1 ))"
    [[ "$rows" == "$expected" ]] || die "$label: ${rows} rows in $dir/summary.csv (expected ${expected})"
    ! grep -qE '<failure>|Exception' "$dir/console.log" || die "$label: errors in $dir/console.log"
    printf '  done: %s (%s conditions)\n' "$dir" "$rows"
}

[[ "$(java -version 2>&1)" == *'"25.0.4.1"'* ]] || die "java is not Temurin 25.0.4.1"

say "check (102 inputs, four collectors)"
bash check.sh | tee /dev/stderr | grep '^PASS: 102 inputs' >/dev/null || die "correctness check failed"

say "build"
rm -rf build/classes build/generated
bash build.sh | tee /dev/stderr | grep -c 'research.skew.AggregationBenchmark\.' | grep -qx 4 \
    || die "expected four benchmarks"

adder='.*parallelConcurrentAdder'
run_one "② LongAdder, base (N x distribution, K=256)" 9 \
    env BENCH="$adder" bash run.sh full
run_one "② LongAdder, K=64 and 8192 (N=1e5)" 6 \
    env BENCH="$adder" bash run.sh full -p size=100000 -p cardinality=64,8192
run_one "① boundary N=1e5, K=1024/2048/4096" 36 \
    bash run.sh full -p size=100000 -p cardinality=1024,2048,4096
run_one "① boundary N=1e6, K=16384/32768/65536" 36 \
    bash run.sh full -p size=1000000 -p cardinality=16384,32768,65536

say "figures"
if [[ -x .venv/bin/python ]]; then
    .venv/bin/python scripts/plot_figures.py
else
    printf 'no .venv: run  .venv/bin/python scripts/plot_figures.py  after setting it up\n'
fi
say "all done"
