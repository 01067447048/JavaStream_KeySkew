#!/usr/bin/env bash
# Diagnostics only (no timing). Results go to results-diag/<timestamp>/.
#   bash diag/run_binhead.sh              # bin-0 state before each hot-key update, default + presized map,
#                                          # hot90 x 3 seeds, 5 runs each (~2 min). Raw CSV + summary.md
#   bash diag/run_binhead.sh cells        # does the hot key's LongAdder stripe? (E1 syncAdder vs casAdder)
#   bash diag/run_binhead.sh detail 100000 2048 20260929   # bin-0 contents per run (console only)
# The non-head share is an observation rate, not a lock-acquisition rate (see BinHeadDiag.java).
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
[[ -f build/classes/research/skew/Workload.class ]] || { echo "run: bash build.sh"; exit 1; }
out="$(mktemp -d)"; trap 'rm -rf "$out"' EXIT
javac -d "$out" -cp build/classes diag/BinHeadDiag.java diag/BinHeadDetail.java diag/AdderCellsDiag.java
opts=(--add-opens java.base/java.util.concurrent=ALL-UNNAMED
      --add-opens java.base/java.util.concurrent.atomic=ALL-UNNAMED
      -Djava.util.concurrent.ForkJoinPool.common.parallelism=3 -cp "build/classes:$out")
dest="results-diag/$(date -u +%Y%m%dT%H%M%SZ)"
case "${1:-binhead}" in
    detail) shift; java "${opts[@]}" BinHeadDetail "$@" ;;
    cells)
        mkdir -p "$dest"
        java "${opts[@]}" AdderCellsDiag | tee "$dest/adder_cells.md"
        printf '\nsaved: %s\n' "$dest/adder_cells.md" ;;
    binhead)
        mkdir -p "$dest"
        { java -version 2>&1; uname -a; } > "$dest/environment.txt"
        for map in default presized; do
            java "${opts[@]}" BinHeadDiag hot90 "$map" 5 > "$dest/binhead_${map}.csv" 2>> "$dest/summary.md"
        done
        cat "$dest/summary.md"
        printf '\nsaved: %s (raw CSV per run + summary.md)\n' "$dest" ;;
    *) echo "usage: bash diag/run_binhead.sh [binhead|cells|detail N K SEED]"; exit 2 ;;
esac
