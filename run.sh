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
# RESULTS_DIR keeps runs from different machines apart (default: results).
results_root="${RESULTS_DIR:-results}"
mkdir -p "$results_root"
output_dir="$(mktemp -d "${results_root}/${mode}-$(date -u +%Y%m%dT%H%M%SZ).XXXXXX")"
{
    date -u
    uname -a
    java -version
    printf 'Mode: %s\n' "$mode"
    printf 'Additional arguments: '; printf '%q ' "$@"; printf '\n'
    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 src/main/java/research/skew/*.java .deps/*.jar
    elif command -v sha256sum >/dev/null 2>&1; then
        sha256sum src/main/java/research/skew/*.java .deps/*.jar
    fi
    if [[ "$(uname -s)" == Darwin ]]; then
        /usr/sbin/sysctl machdep.cpu.brand_string hw.physicalcpu hw.logicalcpu hw.memsize || true
        /usr/bin/sw_vers
    elif [[ "$(uname -s)" == Linux ]]; then
        grep PRETTY_NAME /etc/os-release || true
        lscpu || true
        free -h || true
        printf 'CPU affinity: '; taskset -pc $$ 2>/dev/null || printf 'unknown\n'
        printf 'nproc: '; nproc
        printf 'Governor: '; sort /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null | uniq -c | tr '\n' ' '; printf '\n'
        printf 'intel_pstate no_turbo: '; cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null || printf 'n/a\n'
    fi
} > "$output_dir/environment.txt" 2>&1
java -cp 'build/classes:.deps/*' org.openjdk.jmh.Main \
    'research.skew.AggregationBenchmark.*' \
    -foe true -prof gc -rf json -rff "$output_dir/jmh.json" ${settings[@]+"${settings[@]}"} "$@" \
    2>&1 | tee "$output_dir/console.log"
if command -v python3 >/dev/null 2>&1; then
    python3 scripts/jmh_to_csv.py "$output_dir"
else
    printf '%s\n' 'python3 not found: CSV not written. Convert later with scripts/jmh_to_csv.py' >&2
fi
printf 'Saved: %s\n' "$output_dir"
