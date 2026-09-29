#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
mode="${1:-smoke}"
if [[ "$#" -gt 0 ]]; then shift; fi
case "$mode" in
    smoke) settings=(-p size=10000 -p distribution=uniform,hot90 -f 1 -wi 1 -i 1 -w 200ms -r 200ms) ;;
    full) settings=() ;;
    *) printf '%s\n' 'Usage: bash run.sh smoke|full [additional JMH arguments]' >&2; exit 2 ;;
esac
if [[ ! -f build/classes/META-INF/BenchmarkList ]]; then
    printf '%s\n' 'First run: bash build.sh' >&2
    exit 1
fi
mkdir -p results
output_dir="$(mktemp -d "results/${mode}-$(date -u +%Y%m%dT%H%M%SZ).XXXXXX")"
{
    date -u
    uname -a
    java -version
    printf 'Mode: %s\n' "$mode"
    printf 'Additional arguments: '; printf '%q ' "$@"; printf '\n'
    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 src/main/java/research/skew/*.java .deps/*.jar
    fi
    if [[ "$(uname -s)" == Darwin ]]; then
        /usr/sbin/sysctl machdep.cpu.brand_string hw.physicalcpu hw.logicalcpu hw.memsize || true
        /usr/bin/sw_vers
    fi
} > "$output_dir/environment.txt" 2>&1
java -cp 'build/classes:.deps/*' org.openjdk.jmh.Main \
    'research.skew.AggregationBenchmark.*' \
    -foe true -prof gc -rf json -rff "$output_dir/jmh.json" ${settings[@]+"${settings[@]}"} "$@" \
    2>&1 | tee "$output_dir/console.log"
printf 'Saved: %s\n' "$output_dir"
