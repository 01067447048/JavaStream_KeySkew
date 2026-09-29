#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
mkdir -p .deps build/classes build/generated
fetch() {
    local artifact="$1"
    local filename=".deps/${artifact##*/}"
    if [[ ! -s "$filename" ]]; then
        curl --fail --location --retry 2 --connect-timeout 15 \
            "https://repo.maven.apache.org/maven2/$artifact" -o "$filename.part"
        mv -- "$filename.part" "$filename"
    fi
}
fetch org/openjdk/jmh/jmh-core/1.37/jmh-core-1.37.jar
fetch org/openjdk/jmh/jmh-generator-annprocess/1.37/jmh-generator-annprocess-1.37.jar
fetch net/sf/jopt-simple/jopt-simple/5.0.4/jopt-simple-5.0.4.jar
fetch org/apache/commons/commons-math3/3.6.1/commons-math3-3.6.1.jar
javac --release 17 -cp '.deps/*' \
    -processorpath '.deps/jmh-core-1.37.jar:.deps/jmh-generator-annprocess-1.37.jar' \
    -processor org.openjdk.jmh.generators.BenchmarkProcessor \
    -s build/generated -d build/classes src/main/java/research/skew/*.java
java -cp 'build/classes:.deps/*' org.openjdk.jmh.Main -l
