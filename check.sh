#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
mkdir -p build/check
javac --release 17 -d build/check src/main/java/research/skew/Workload.java src/main/java/research/skew/Validation.java
java -Xms512m -Xmx512m -Djava.util.concurrent.ForkJoinPool.common.parallelism=3 -cp build/check research.skew.Validation
