#!/usr/bin/env bash
# Environment B (Ubuntu, Intel i5-8250U) runner. See 환경B용실험안내서.md.
#
#   bash run_envB.sh            # all stages: preflight check build main boundary diag pack
#   bash run_envB.sh preflight  # one stage only (preflight|check|build|main|boundary|diag|pack)
#
# Options (environment variables):
#   PIN=0             do not pin to one logical CPU per physical core (default PIN=1)
#   SKIP_BOUNDARY=1   skip the N/K boundary runs (about 40 minutes)
#   SKIP_DIAG=1       skip the perf counter stage
#   ALLOW_WRONG_JDK=1 continue even if java is not Temurin 25.0.4.1 (not for the paper)
set -euo pipefail
cd -- "$(dirname -- "$0")"

EXPECTED_JDK="25.0.4.1"
MAIN_DIR="results-envB"          # timing runs (used for figures)
DIAG_DIR="results-envB-diag"     # perf counter runs (never mixed with timing)
SYS_DIR="$MAIN_DIR/system"
PIN="${PIN:-1}"
STAGE="${1:-all}"

mkdir -p "$SYS_DIR"
LOG="$SYS_DIR/run_envB.log"
exec > >(tee -a "$LOG") 2>&1

say()  { printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
warn() { printf '  경고: %s\n' "$*"; }
die()  { printf '\n오류: %s\n' "$*"; exit 1; }

# One logical CPU per physical core (skips hyper-threading siblings).
physical_cpus() {
    lscpu -p=CPU,CORE,SOCKET | grep -v '^#' | awk -F, '!seen[$3","$2]++ {print $1}' | paste -sd, -
}

pin_prefix() {
    if [[ "$PIN" == 1 ]]; then
        printf 'taskset -c %s' "$(physical_cpus)"
    fi
}

stage_preflight() {
    say "1/7 사전 점검"
    [[ "$(uname -s)" == Linux ]] || die "Linux 전용 스크립트다. macOS에서는 run.sh를 쓴다."
    command -v java >/dev/null || die "java가 없다. 안내서 2절대로 JDK를 설치하고 PATH를 설정한다."
    local version
    version="$(java -version 2>&1)"
    version="${version%%$'\n'*}"
    printf '  java: %s\n' "$version"
    if [[ "$version" != *"\"$EXPECTED_JDK\""* ]]; then
        if [[ "${ALLOW_WRONG_JDK:-0}" == 1 ]]; then
            warn "JDK가 $EXPECTED_JDK 이 아니다. 이 결과는 논문에 쓰지 않는다."
        else
            die "JDK가 $EXPECTED_JDK 이 아니다. 안내서 2절을 확인한다."
        fi
    fi
    command -v javac >/dev/null || die "javac가 없다. JRE가 아니라 JDK를 설치한다."
    command -v python3 >/dev/null || warn "python3가 없어 CSV가 만들어지지 않는다. sudo apt install python3"
    command -v taskset >/dev/null || die "taskset이 없다. sudo apt install util-linux"
    local jmh_pids
    if jmh_pids="$(pgrep -f 'org.openjdk.jmh.Main')"; then
        ps -o pid,stat,etime,command -p "$(echo "$jmh_pids" | paste -sd, -)" | cut -c1-120
        die "다른 JMH가 실행 중이다(STAT이 T면 Ctrl+Z로 멈춘 것). fg 후 Ctrl+C 하거나 kill <pid>로 끝낸다."
    fi

    local governors no_turbo ac
    governors="$(sort /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null | uniq -c | xargs)"
    no_turbo="$(cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null || echo n/a)"
    ac="$(cat /sys/class/power_supply/*/online 2>/dev/null | head -1 || true)"
    printf '  주파수 정책: %s\n' "${governors:-알 수 없음}"
    printf '  터보 끔(no_turbo): %s\n' "$no_turbo"
    printf '  전원 연결(online): %s\n' "${ac:-알 수 없음}"
    printf '  고정할 CPU(물리 코어당 1개): %s (PIN=%s)\n' "$(physical_cpus)" "$PIN"
    [[ "$governors" == *performance* && "$governors" != *powersave* ]] \
        || warn "주파수 정책이 performance가 아니다. 안내서 3.2절의 명령을 권장한다(선택)."
    [[ "$ac" == 0 ]] && warn "배터리로 동작 중이다. 전원을 연결한다."
    local busy
    busy="$(ps -eo pcpu= | awk '{s+=$1} END {printf "%d", s}')"
    printf '  프로세스 CPU 사용률 합(대략): %s%%\n' "$busy"
    (( busy > 50 )) && warn "다른 프로그램이 CPU를 쓰고 있다. 측정 전에 끈다."

    {
        date -u
        uname -a
        grep PRETTY_NAME /etc/os-release || true
        java -version 2>&1
        printf '\n## lscpu\n'; lscpu
        printf '\n## lscpu -e\n'; lscpu -e
        printf '\n## free -h\n'; free -h
        printf '\n## governor\n%s\n' "$governors"
        printf 'no_turbo: %s\nAC online: %s\n' "$no_turbo" "$ac"
        printf 'pinned CPUs (PIN=%s): %s\n' "$PIN" "$(physical_cpus)"
        printf 'perf_event_paranoid: %s\n' "$(cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || echo n/a)"
    } > "$SYS_DIR/system_info.txt" 2>&1
    printf '  기록: %s\n' "$SYS_DIR/system_info.txt"
}

stage_check() {
    say "2/7 정확성 검사 (102개 입력, 집계 방식 4개)"
    bash check.sh | tee "$SYS_DIR/check.log"
    grep -q '^PASS: 102 inputs' "$SYS_DIR/check.log" || die "정확성 검사가 102개 입력을 통과하지 못했다."
}

stage_build() {
    say "3/7 빌드"
    rm -rf build/classes build/generated
    bash build.sh | tee "$SYS_DIR/build.log"
    local n
    n="$(grep -c 'research.skew.AggregationBenchmark\.' "$SYS_DIR/build.log" || true)"
    [[ "$n" == 4 ]] || die "벤치마크 4개가 등록되지 않았다(발견: $n)."
}

run_one() {  # label, expected rows, JMH args...
    local label="$1" expected="$2"; shift 2
    say "  실행: $label"
    # shellcheck disable=SC2046
    RESULTS_DIR="$MAIN_DIR" $(pin_prefix) bash run.sh full "$@"
    local dir
    dir="$(ls -dt "$MAIN_DIR"/full-* | head -1)"
    local rows
    rows="$(( $(wc -l < "$dir/summary.csv") - 1 ))"
    if [[ "$rows" != "$expected" ]]; then
        die "$label: summary.csv가 ${rows}줄이다(기대: ${expected}). $dir/console.log 확인."
    fi
    if grep -qE '<failure>|Exception' "$dir/console.log"; then
        die "$label: console.log에 오류가 있다. $dir/console.log 확인."
    fi
    printf '  완료: %s (%s개 조건)\n' "$dir" "$rows"
}

stage_main() {
    say "4/7 본 측정 (36 + 12 + 12 + 12 = 72개 조건, 방식 4개)"
    [[ -f build/classes/META-INF/BenchmarkList ]] || die "빌드가 없다. bash run_envB.sh build"
    run_one "기본 측정" 36
    run_one "추가 검증 ①-a K=64" 12 -p size=100000 -p cardinality=64
    run_one "추가 검증 ①-b K=8192" 12 -p size=100000 -p cardinality=8192
    run_one "추가 검증 ② Seed 20260930" 12 -p size=100000 -p seed=20260930
}

stage_boundary() {
    say "5/7 N/K 경계 검증 (36 + 36 = 72개 조건)"
    if [[ "${SKIP_BOUNDARY:-0}" == 1 ]]; then
        printf '  SKIP_BOUNDARY=1: 건너뜀\n'; return
    fi
    [[ -f build/classes/META-INF/BenchmarkList ]] || die "빌드가 없다. bash run_envB.sh build"
    run_one "경계 N=10^5, K=1024/2048/4096" 36 -p size=100000 -p cardinality=1024,2048,4096
    run_one "경계 N=10^6, K=16384/32768/65536" 36 -p size=1000000 -p cardinality=16384,32768,65536
}

stage_diag() {
    say "6/7 원인 계측 (perf 하드웨어 카운터, 선택)"
    if [[ "${SKIP_DIAG:-0}" == 1 ]]; then
        printf '  SKIP_DIAG=1: 건너뜀\n'; return
    fi
    if ! command -v perf >/dev/null || ! perf stat -e cycles,instructions true >/dev/null 2>&1; then
        warn "perf를 쓸 수 없어 건너뛴다. 안내서 5절(perf 설치, perf_event_paranoid)을 확인한다."
        return
    fi
    # Timing is disturbed by perf; these runs go to DIAG_DIR and are never plotted.
    # shellcheck disable=SC2046
    RESULTS_DIR="$DIAG_DIR" $(pin_prefix) bash run.sh full \
        -p size=100000 -p cardinality=256 -p distribution=uniform,hot90 \
        -f 1 -prof perfnorm
    printf '  완료: %s (카운터는 각 결과 폴더의 secondary.csv)\n' "$(ls -dt "$DIAG_DIR"/full-* | head -1)"
}

stage_pack() {
    say "7/7 결과 묶기"
    local out="envB-results-$(hostname -s)-$(date +%Y%m%d-%H%M).tar.gz"
    local dirs=("$MAIN_DIR")
    [[ -d "$DIAG_DIR" ]] && dirs+=("$DIAG_DIR")
    tar -czf "$out" "${dirs[@]}"
    printf '  만든 파일: %s (%s)\n' "$(pwd)/$out" "$(du -h "$out" | cut -f1)"
    printf '  이 파일을 주저자에게 보낸다.\n'
}

case "$STAGE" in
    preflight) stage_preflight ;;
    check) stage_check ;;
    build) stage_build ;;
    main) stage_preflight; stage_main ;;
    boundary) stage_preflight; stage_boundary ;;
    diag) stage_diag ;;
    pack) stage_pack ;;
    all)
        start=$(date +%s)
        stage_preflight; stage_check; stage_build; stage_main; stage_boundary; stage_diag; stage_pack
        say "전체 완료: $(( ($(date +%s) - start) / 60 ))분 소요"
        ;;
    *) die "알 수 없는 단계: $STAGE (preflight|check|build|main|boundary|diag|pack|all)" ;;
esac
