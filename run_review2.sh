#!/usr/bin/env bash
# Extra experiments requested by AstraReview2 (environment A). About 30 minutes (estimate).
#
#   bash run_review2.sh                  # all three steps, in this order
#   STEPS="E3 E1b" bash run_review2.sh   # choose steps
#
#   E3  (review 5.3, ~6 min)  bin-head position on a fixed map: hot key first vs second node,
#                             computeIfAbsent vs get, no resize          -> results-e3/
#   E1b (review 5.2, ~10 min) same-counter monitor comparison: syncAtomic vs casAtomic,
#                             syncAdder vs casAdder (+ syncLong baseline) -> results-e1b/
#   E2  (review 5.5, ~14 min) stability re-measurement with long warmup (2 s x 10, 2 s x 5,
#                             5 forks) of two conditions                 -> results-e2/
# Each step writes <dir>/summary.md. The paper figures (results/) are not affected.
set -euo pipefail
cd -- "$(dirname -- "$0")"

STEPS="${STEPS:-E3 E1b E2}"

say() { printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
die() { printf '\nerror: %s\n' "$*"; exit 1; }

[[ "$(java -version 2>&1)" == *'"25.0.4.1"'* ]] || die "java is not Temurin 25.0.4.1"
if pids="$(pgrep -f 'org.openjdk.jmh.Main')"; then
    ps -o pid,stat,etime,command -p "$(echo "$pids" | paste -sd, -)" | cut -c1-120
    die "another JMH is running (STAT T = suspended by Ctrl+Z). Stop it first: fg then Ctrl+C, or kill <pid>"
fi
for b in BinHeadBenchmark.computeIfAbsent ControlBenchmark.syncAtomic; do
    grep -q "$b" build/classes/META-INF/BenchmarkList 2>/dev/null || die "build has no $b. Run: bash build.sh"
done

say "check (correctness, nine collectors)"
bash check.sh | tee /dev/stderr | grep '^PASS: 102 inputs' >/dev/null || die "correctness check failed"

run_one() {  # results dir, label, expected rows, JMH args...
    local root="$1" label="$2" expected="$3"; shift 3
    say "run: $label"
    RESULTS_DIR="$root" bash run.sh full "$@"
    local dir rows
    dir="$(ls -dt "$root"/full-* | head -1)"
    rows="$(( $(wc -l < "$dir/summary.csv") - 1 ))"
    [[ "$rows" == "$expected" ]] || die "$label: ${rows} rows in $dir/summary.csv (expected ${expected})"
    ! grep -qE '<failure>|Exception' "$dir/console.log" || die "$label: errors in $dir/console.log"
    grep -q 'common.parallelism=3' "$dir/console.log" || die "$label: pool parallelism setting missing"
    printf '  done: %s (%s rows)\n' "$dir" "$rows"
}

summarize() {  # step name, results dir
    python3 scripts/review2_summary.py "$1" "$2" | tee "$2/summary.md"
    say "saved: $2/summary.md"
}

for step in $STEPS; do
    case "$step" in
        E3)
            export BENCH='research.skew.BinHeadBenchmark.*'
            run_one results-e3 "E3: fixed map, hot key head/second, N=1e5 and 1e6" 8 \
                -p size=100000,1000000 -p position=head,second -p seed=20260929
            dir="$(ls -dt results-e3/full-* | head -1)"
            n="$(grep -c 'Verify: .* OK' "$dir/console.log" || true)"
            [[ "$n" == 24 ]] || die "E3: expected 24 'Verify ... OK' lines (8 rows x 3 forks), found $n"
            summarize E3 results-e3 ;;
        E1b)
            export BENCH='research.skew.ControlBenchmark.*'
            run_one results-e1b "E1b: five counters, N=1e5, K=256" 15 \
                -p size=100000 -p cardinality=256 -p distribution=uniform,hot50,hot90 -p seed=20260929
            summarize E1b results-e1b ;;
        E2)
            long=(-wi 10 -w 2s -i 5 -r 2s -f 5)
            export BENCH='AggregationBenchmark\.(sequential|parallelMerge)$'
            run_one results-e2 "E2a: N=1e4, K=256, hot90, sequential/merge (long warmup)" 2 \
                -p size=10000 -p cardinality=256 -p distribution=hot90 -p seed=20260929 "${long[@]}"
            export BENCH='AggregationBenchmark\.(sequential|parallelMerge|parallelConcurrent)$'
            run_one results-e2 "E2b: N=1e6, K=32768, uniform, three stock collectors (long warmup)" 3 \
                -p size=1000000 -p cardinality=32768 -p distribution=uniform -p seed=20260929 "${long[@]}"
            summarize E2 results-e2 ;;
        *) die "unknown step: $step (use E3, E1b, E2)" ;;
    esac
done
say "all requested steps finished: $STEPS"
