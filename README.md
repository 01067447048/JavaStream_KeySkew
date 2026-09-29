# Java Stream 키 편향 집계 실험

연구 질문과 조건의 정의는 [연구계획](연구계획.md)에 있다. **현재는 실험 준비 단계이며 논문용 성능 결론은 없다.**

## 파일

- `src/main/java/research/skew/Workload.java`: 정확한 빈도·고정 고유 키 수의 입력 생성기와 세 집계 구현.
- `src/main/java/research/skew/Validation.java`: 입력 분포, 재현성, 모든 키의 집계 결과 검증.
- `src/main/java/research/skew/AggregationBenchmark.java`: JMH(Java Microbenchmark Harness; 자바 성능 측정 도구) 설정과 측정 코드.
- `check.sh`: 외부 의존성 없이 정확성 검사.
- `build.sh`: 실험 폴더 안으로 필요한 네 라이브러리를 내려받고 빌드.
- `run.sh`: 동작 확인 또는 본 측정. 실행마다 새로운 결과 폴더를 생성.
- `run_envB.sh`: 환경 B(Ubuntu, Intel i5-8250U)용 전체 실행 스크립트. 사전 점검, 정확성 검사, 빌드, 본 측정 4회, 선택적 perf 계측, 결과 묶기를 한 번에 수행. 결과는 `results-envB/`에 따로 저장. 사용법은 `환경B용실험안내서.md`.
- `scripts/jmh_to_csv.py`: 결과 폴더의 `jmh.json`을 `summary.csv`·`raw.csv`로 변환. `run.sh`가 매 실행 후 자동 호출.
- `scripts/plot_figures.py`: 모든 본 측정 결과를 모아 논문 그림 3개와 선택 기준 표 생성.
- `requirements.txt`: 그림 스크립트용 Python 패키지(matplotlib).
- `pom.xml`: Maven(자바 프로젝트 빌드 도구)을 사용하는 환경용 대체 빌드 설정.

## 실행

Terminal(명령 실행 창)에서 이 폴더를 현재 디렉터리로 연 뒤 아래 명령을 사용한다. JDK(자바 개발 도구) 17 이상이 필요하다. **본 측정 JDK는 Eclipse Temurin 25.0.4.1 LTS**(`~/Library/Java/JavaVirtualMachines/temurin-25.0.4.1`)다. 처음 동작 확인은 OpenJDK 24.0.2에서 했으며, 그 빌드 산출물과 수치는 본 측정에 섞지 않는다. 실행 전 `java -version`이 25.0.4.1인지 확인한다. 기본 명령은 macOS와 Linux용이다.

```bash
bash check.sh
bash build.sh
bash run.sh smoke
```

`check.sh`는 3개 분포 × 2개 난수 초기값에 대해 다음 입력 크기·고유 키 수 조합을 검증한다. 기본 측정 조건 27개와는 다른 숫자다.

- K=64, 256: N=10,000·100,000·1,000,000 → 36개
- K=8192: N=100,000·1,000,000 → 12개. N=10,000은 hot90에서 나머지 키에 줄 데이터가 부족해 제외
- 합계 48개

`build.sh`는 JMH 1.37, 그 코드 생성기, jopt-simple 5.0.4, commons-math3 3.6.1을 Maven Central(자바 라이브러리 저장소)에서 `.deps`에 저장한다. 최초 실행에는 네트워크 연결이 필요하다. 전역 Java 설정을 변경하지 않는다.

`smoke`(동작 확인)는 N=10,000에서 균등·90% 집중 분포에 대해 세 구현을 짧게 실행한다. 각 조건의 예열과 측정이 각각 200 ms 한 번뿐이므로, 결과 숫자는 **논문에 사용하지 않는다**.

본 측정:

```bash
bash run.sh full
```

추가 고유 키 수 검증, 각 9개 조건. 기본 측정의 N=100,000·K=256 결과와 함께 K=64·256·8192 세 값을 비교한다.

```bash
bash run.sh full -p size=100000 -p cardinality=64
```

```bash
bash run.sh full -p size=100000 -p cardinality=8192
```

K=8192는 N=100,000 이상에서만 사용한다. N=10,000에서는 입력 생성이 실패하고, `-foe true` 설정 때문에 실행 전체가 멈춘다. N=100,000·hot90에서는 나머지 8,191개 키가 키당 1–2개 원소만 가진다.

다른 입력 순서의 대표 조건 검증, 9개 조건:

```bash
bash run.sh full -p size=100000 -p seed=20260930
```

JMH는 부모 프로세스와 자식 JVM(자바 가상 머신) 사이의 로컬 통신을 사용한다. 실행 제한 환경에서는 이 통신 때문에 실패할 수 있다. 결과 파일이 생성됐다는 사실만으로 성공으로 판단하지 말고, `console.log`(실행 기록)의 오류와 완료 여부를 확인한다.

## 결과 읽기

`results/실행종류-시간.고유값/` 아래에 다음을 저장한다.

- `environment.txt`: 실행 환경, 코드와 라이브러리의 SHA-256(내용 검증 해시), 추가 인자.
- `console.log`: JMH 전체 실행 기록. 실제 입력 비중·공유 풀 병렬성·인식된 프로세서 수도 포함.
- `jmh.json`: JSON(구조화된 데이터 형식) 원시 측정 결과.
- `summary.csv`: 조건별 한 줄. 평균 실행시간(ms), JMH 99.9% 신뢰구간, 원소 기준 처리량, 할당 바이트/op, GC 횟수·시간, JDK·JMH 설정.
- `raw.csv`: 반복별 한 줄. 실행시간과 할당 바이트의 독립 JVM(fork)·반복 번호별 원시값.

두 CSV는 `run.sh`가 측정 직후 `scripts/jmh_to_csv.py`(Python 표준 라이브러리만 사용)로 자동 생성한다. CSV가 없는 예전 결과 폴더는 `python3 scripts/jmh_to_csv.py results/<폴더>`로 변환한다. 예열이 1회뿐인 smoke 결과는 신뢰구간이 비어 있다.

## 그림과 선택 기준 표

그림 스크립트는 matplotlib이 필요하다. 전역 Python을 건드리지 않도록 프로젝트 안의 가상환경에 설치한다(최초 1회, 네트워크 필요).

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

본 측정 결과(`results/full-*`)가 쌓이면 다음 명령으로 `figures/`에 그림과 표를 만든다.

```bash
.venv/bin/python scripts/plot_figures.py
```

| 출력 | 내용 | 필요한 실행 |
|---|---|---|
| `fig1_scaling.pdf/.png` | 균등 분포·K=256에서 N별 실행시간(로그-로그) | 기본 측정 |
| `fig2_skew.pdf/.png` | K=256에서 분포별 실행시간, N=10⁵·10⁶ 두 패널 | 기본 측정 |
| `fig3_cardinality.pdf/.png` | N=10⁵에서 K=64·256·8192별 실행시간과 할당 KiB/op, 분포별 세 열 | 기본 측정 + K 추가 검증 두 개 |
| `table2_selection.csv/.md` | 조건별 가장 빠른 방식. 2위와 신뢰구간이 겹치면 `tie (CI overlap)` | 모든 측정 |
| `combined_summary.csv` | 그림에 사용한 모든 행 | 모든 측정 |

- 같은 조건을 여러 번 측정했다면 가장 최근 실행을 쓰고, 어느 실행이 대체됐는지 화면에 출력한다.
- 그림은 기본 Seed(20260929)만 사용한다. 입력 순서 검증(Seed 20260930)은 표와 `combined_summary.csv`에만 들어간다.
- 조건이 부족한 그림은 건너뛰고 이유를 출력한다.
- 오차 막대는 JMH 99.9% 신뢰구간이다. PDF는 글꼴을 내장(Type 42)하므로 IEEE 원고에 바로 넣을 수 있다.
- `--include-smoke`는 smoke 결과까지 읽는다. 배치를 확인하는 용도이며, 그 그림은 논문에 쓰지 않는다.

기본 결과 단위는 `ms/op`(전체 배열 집계 1회당 밀리초)다. `gc.alloc.rate.norm`(집계 1회당 할당 바이트)은 입력 생성 비용을 포함하지 않는다. 할당률 자체만으로 캐시 미스나 메모리 대역폭을 추정하지 않는다.

원시 결과의 `rawData`(반복별 원시 측정값)를 보존한다. 독립 JVM 반복과 입력 난수 초기값 변경을 구분한다. 격차가 작거나 반복 변동이 크면 승자를 단정하지 않는다.

## Maven을 사용하는 경우

공식 JMH 안내는 독립 Maven 프로젝트를 권한다. Maven이 준비된 다른 장비에서는 다음 대체 경로도 사용할 수 있다. 현재 제공하는 기본 실행 절차와 섞지 말고 선택한 경로·JDK를 기록한다. 이 Maven 경로는 별도 실행 검증이 필요하다.

```bash
mvn clean package
java -jar target/benchmarks.jar -l
java -jar target/benchmarks.jar -foe true -prof gc -rf json -rff measured-results.json
```

## 동작 검증 기록

- 2026-09-29: OpenJDK 24.0.2에서 JDK만 사용하는 정확성 검사 통과. 36개 입력, 각 입력의 세 집계 결과가 독립 반복문 정답과 일치.
- JMH 코드 생성·컴파일 완료, 세 측정 항목이 정상 등록됨.
- `results/smoke-20260929T083416Z.jS7Y45/`: 6개 조건의 짧은 동작 확인 완료. 구조화된 결과 6개와 할당 계측이 저장됨. 예열·반복이 부족하므로 성능 비교 결론에는 사용하지 않음.
- 위 동작 확인 환경: Apple M5, 물리·논리 프로세서 각 10개, 메모리 32 GiB, macOS 26.6.2, OpenJDK 24.0.2. 본 측정 환경은 실행 시 다시 기록.
- `results/smoke-20260929T083403Z.IaHp19/`: 실행 제한 환경에서 로컬 통신이 차단된 최초 실패 기록. 유효한 측정 결과가 아님. 이후 필요한 실행 권한을 통해 위의 성공 실행을 완료함.
- 본 측정 27개 조건의 성능 결과는 아직 없음.
- 2026-09-29: `run.sh full` 수정. macOS 기본 bash 3.2에서 빈 설정 배열이 `set -u` 오류를 내던 문제를 고침(`${settings[@]+"${settings[@]}"}`). 수정 후 JMH 실행으로는 아직 검증하지 않음.
- 2026-09-29: 본 측정 JDK를 Eclipse Temurin 25.0.4.1 LTS로 변경. JDK 25의 `Collectors.java`에서 `counting()`이 `summingLong` 기반이고, `groupingByConcurrent`가 동시 갱신을 지원하지 않는 하위 집계에 `synchronized`를 적용함을 다시 확인(1283행).
- JDK 25로 바꾼 뒤 `bash check.sh`와 `bash build.sh`를 다시 실행해야 함. 기존 `build/`는 JDK 24로 컴파일된 산출물이다.
- 2026-09-29: K=8192 추가 검증 조건 추가. `Validation.java`의 검사 대상이 36개에서 48개 입력으로 늘었으며, JDK 25에서 아직 실행하지 않음.
- 2026-09-29: CSV 자동 저장과 그림 스크립트 추가. CSV 변환은 기존 smoke 결과의 복사본으로 동작을 확인함(6개 조건, 원시값 12개). `run.sh` 안에서의 자동 호출은 실제 측정으로 아직 실행하지 않음.
- 2026-09-29: `.venv`에 matplotlib 3.11.2 설치. 그림 스크립트는 프로젝트 밖 임시 폴더에서 **가짜 수치**로 배치(글자 겹침, 눈금, 범례)만 확인함. 실제 측정 그림은 아직 없음.
- 2026-09-29 20:05: 새로 측정하기 위해 기존 `results/` 폴더(smoke 결과 3개)를 휴지통으로 옮김(`~/.Trash/JavaStream_키편향-results-20260929-200544`). 위 기록에 나오는 smoke 폴더는 더 이상 프로젝트 안에 없다.
- 2026-09-29: 환경 B 준비. `run.sh`에 `RESULTS_DIR`(결과 폴더 지정)과 Linux 환경 기록(`lscpu`, `free -h`, CPU 고정 상태, 주파수 정책, 터보 상태) 추가. `jmh_to_csv.py`가 모든 보조 지표를 `secondary.csv`로도 저장. `run_envB.sh`는 macOS에서 문법 검사만 했으며 Linux에서는 아직 실행하지 않음.
- 환경 B 결과로 그림을 만들 때: `.venv/bin/python scripts/plot_figures.py --results results-envB --out figures-envB`. 환경 A와 B의 결과를 한 폴더에 섞지 않는다.
- 장비의 코어 구성: 성능 코어 4개와 효율 코어 6개(`sysctl hw.perflevel0.physicalcpu`, `hw.perflevel1.physicalcpu`). 공용 풀 병렬성 3과 호출 스레드 1개를 합치면 4로, 성능 코어 수와 같다. macOS에서는 스레드를 특정 코어에 고정할 수 없으므로 효율 코어에서 실행될 가능성은 남는다.
