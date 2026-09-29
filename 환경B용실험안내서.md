# 환경 B 실험 안내서

작성일: 2026-09-29
대상: Ubuntu 장비에서 실험을 실행할 공동저자
목표: 환경 A(Apple M5)와 **똑같은 실험**을 환경 B(Intel i5-8250U)에서 실행하고 결과 묶음 하나를 주저자에게 보낸다.

---

## 0. 한눈에 보기

| 항목 | 내용 |
|---|---|
| 받을 파일 | `JavaStream_keyskew_envB.tar.gz` (약 2.6 MB. 코드, 스크립트, JMH 라이브러리 포함) |
| 설치할 것 | Eclipse Temurin JDK **25.0.4.1** (2절) |
| 실행 명령 | `bash run_envB.sh` 하나 (4절) |
| 예상 소요 시간 | 약 30–45분. 측정 시간은 JMH 설정으로 고정되어 있어 장비가 느려도 크게 늘지 않는다(환경 A는 약 29분). 추정값이다 |
| 보낼 파일 | `envB-results-<호스트명>-<날짜>.tar.gz` (6절) |
| 측정 중 할 일 | 전원 연결, 다른 프로그램 끄기, 절전 모드 방지. 컴퓨터를 쓰지 않는다 |

**환경 B의 사양**

| 항목 | 값 |
|---|---|
| OS | Ubuntu 24.04.2 LTS |
| 커널 | Linux 6.11.0-21-generic |
| CPU | Intel Core i5-8250U (4코어 8스레드) |
| 메모리 | DDR4 SDRAM 20 GB |

---

## 1. 준비물 확인

- [ ] 전원 어댑터 연결
- [ ] 인터넷 연결 (JDK를 내려받을 때만 필요)
- [ ] `sudo` 권한 (선택 항목인 3.2절, 5절에서만 필요)
- [ ] 약 1시간 동안 장비를 쓰지 않을 수 있는 시간

---

## 2. JDK 25.0.4.1 설치

**두 환경의 결과를 비교하려면 JDK 버전이 정확히 같아야 한다.** Ubuntu 기본 저장소의 OpenJDK는 쓰지 않는다. 아래 명령을 차례로 실행한다.

### 2.1 내려받기와 무결성 확인

```bash
mkdir -p ~/jdk && cd ~/jdk
```

```bash
curl -LO https://github.com/adoptium/temurin25-binaries/releases/download/jdk-25.0.4.1%2B1/OpenJDK25U-jdk_x64_linux_hotspot_25.0.4.1_1.tar.gz
```

```bash
echo "dbb698396d478e7fa2b1e50f4103324b2a99b90569ee27c33f2261f9215cf41e  OpenJDK25U-jdk_x64_linux_hotspot_25.0.4.1_1.tar.gz" | sha256sum -c -
```

`OK`가 나와야 한다. `FAILED`가 나오면 파일을 지우고 다시 받는다. 파일 크기는 약 135 MB(141,329,719 bytes)다. 체크섬은 Adoptium 공식 API가 공개한 값이다.

### 2.2 압축 풀기와 PATH 설정

```bash
tar -xzf OpenJDK25U-jdk_x64_linux_hotspot_25.0.4.1_1.tar.gz
```

```bash
echo 'export JAVA_HOME="$HOME/jdk/jdk-25.0.4.1+1"' >> ~/.bashrc
```

```bash
echo 'export PATH="$JAVA_HOME/bin:$PATH"' >> ~/.bashrc
```

```bash
source ~/.bashrc
```

### 2.3 확인

```bash
java -version
```

첫 줄이 다음과 같아야 한다.

```
openjdk version "25.0.4.1" 2026-08-18 LTS
```

`javac -version`도 `javac 25.0.4.1`을 출력해야 한다. 다른 버전이 나오면 새 터미널을 열거나 `which java`로 경로를 확인한다.

---

## 3. 측정 전 환경 준비

### 3.1 필수

1. 전원 어댑터를 연결한다.
2. 브라우저, IDE, 메신저 등 다른 프로그램을 모두 끈다.
3. 화면 잠금과 절전은 4절의 `systemd-inhibit` 명령이 막아 준다. 노트북 덮개는 닫지 않는다.

### 3.2 권장 (선택, sudo 필요): CPU 주파수 정책 고정

노트북 CPU는 주파수가 수시로 바뀌어 측정값이 흔들린다. 측정 동안만 `performance`로 고정한다.

현재 정책 확인:

```bash
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort | uniq -c
```

`performance`로 바꾸기:

```bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

측정이 끝나면 원래 값(대개 `powersave`)으로 되돌린다:

```bash
echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

- 바꾸지 않아도 실험은 된다. 스크립트가 경고만 출력하고, 실제 정책을 결과에 기록한다.
- 터보 부스트는 끄지 않는다. 상태만 기록한다.

---

## 4. 실행

### 4.1 압축 풀기

받은 파일을 홈 폴더에 두었다고 가정한다.

```bash
cd ~ && tar -xzf JavaStream_keyskew_envB.tar.gz && cd JavaStream_keyskew
```

한글 이름의 문서 파일(연구계획 등)이 Ubuntu에서 자모가 분리되어 보일 수 있다. 실험에는 영향이 없다.

### 4.2 전체 실행 (권장)

```bash
systemd-inhibit --what=sleep:idle --why="JMH benchmark" bash run_envB.sh
```

`systemd-inhibit`는 실행 중 절전과 화면 잠금을 막는다. 명령이 없으면 `bash run_envB.sh`만 실행하고 절전 설정을 직접 끈다.

### 4.3 스크립트가 하는 일

| 단계 | 이름 | 하는 일 | 성공 기준 |
|---|---|---|---|
| 1/6 | preflight | Linux·JDK 25.0.4.1·`javac`·`taskset` 확인. 주파수 정책, 터보, 전원, CPU 사용률 점검. 시스템 정보를 `results-envB/system/system_info.txt`에 저장 | JDK가 다르면 즉시 중단 |
| 2/6 | check | `check.sh`로 입력 48개와 세 집계 방식의 결과 일치 검사 | `PASS: 48 inputs` |
| 3/6 | build | 이전 빌드를 지우고 JDK 25로 다시 컴파일 | 벤치마크 3개 등록 |
| 4/6 | main | 본 측정 4회 실행 (아래 표) | 실행마다 `summary.csv` 줄 수와 오류 여부 확인 |
| 5/6 | diag | `perf` 하드웨어 카운터 측정(선택). `perf`를 쓸 수 없으면 자동으로 건너뜀 | 5절 |
| 6/6 | pack | 결과를 `envB-results-*.tar.gz` 하나로 묶음 | 파일 경로 출력 |

**4/6 단계의 측정 네 가지** (환경 A와 같다. 정의는 `실험과정및정의내역.md`)

| 순서 | 실험 | 조건 수 |
|---|---|---|
| ① | 기본 측정: N 10⁴·10⁵·10⁶ × 분포 3 × 방식 3, K=256 | 27 |
| ② | 추가 검증: N=10⁵, K=64 | 9 |
| ③ | 추가 검증: N=10⁵, K=8192 | 9 |
| ④ | 추가 검증: N=10⁵, Seed 20260930 | 9 |

**코어 고정.** i5-8250U는 물리 코어 4개에 하이퍼스레딩으로 논리 CPU가 8개다. 스크립트는 `taskset`으로 **물리 코어마다 논리 CPU 하나씩**(보통 `0,1,2,3`)에만 실행한다. 벤치마크는 공용 풀 3개와 호출 스레드 1개, 모두 4개의 스레드로 일한다. 같은 물리 코어를 두 스레드가 나눠 쓰는 간섭을 없애기 위해서다. 코어 고정 없이 돌리려면 `PIN=0 bash run_envB.sh`를 쓴다. 주저자가 요청할 때만 쓴다.

### 4.4 진행 중 화면

- JMH가 조건마다 `# Warmup Iteration`, `Iteration` 줄을 출력한다. 멈춘 것처럼 보여도 1초마다 한 줄씩 진행된다.
- 실행이 하나 끝날 때마다 `완료: results-envB/full-... (27개 조건)`처럼 출력된다.
- 마지막에 `전체 완료: N분 소요`가 나오면 끝이다.
- 화면 전체 기록은 `results-envB/system/run_envB.log`에 저장된다.

---

## 5. (선택) perf 하드웨어 카운터 측정

환경 A(macOS)에서는 할 수 없던 측정이다. 병렬 공유 방식이 느린 원인(캐시 미스 등)을 뒷받침하는 데 쓴다. **안 해도 본 실험은 완전하다.** 약 2–3분 걸린다.

**준비 (sudo 필요)**

```bash
sudo apt install linux-tools-common linux-tools-$(uname -r)
```

```bash
cat /proc/sys/kernel/perf_event_paranoid
```

값이 2보다 크면 측정하는 동안만 낮춘다:

```bash
sudo sysctl -w kernel.perf_event_paranoid=1
```

확인:

```bash
perf stat -e cycles,instructions true
```

오류 없이 카운터 값이 출력되면 준비된 것이다.

**측정 내용**

- 조건: N=10⁵, K=256, 균등·hot90, 세 방식 = 6개 조건. JVM 1회
- JMH `-prof perfnorm`으로 집계 1회당 사이클, 명령어, 캐시 미스 등을 기록
- perf가 실행시간에 영향을 주므로 결과는 `results-envB-diag/`에 따로 저장한다. **그림에는 쓰지 않는다.**

4.2의 전체 실행 전에 준비해 두면 자동으로 포함된다. 전체 실행이 이미 끝났다면 아래 명령으로 이 단계와 묶기만 다시 실행한다.

```bash
bash run_envB.sh diag && bash run_envB.sh pack
```

**끝나면 원래 값으로 되돌린다** (처음 값이 4였다면):

```bash
sudo sysctl -w kernel.perf_event_paranoid=4
```

---

## 6. 결과 확인과 보내기

### 6.1 보낼 파일

프로젝트 폴더에 `envB-results-<호스트명>-<날짜>.tar.gz`가 생긴다. **이 파일 하나만 주저자에게 보낸다.** 안에는 다음이 들어 있다.

```
results-envB/
├── system/                  # system_info.txt, check.log, build.log, run_envB.log
├── full-<시각>.<값>/         # ① 기본 측정 (27)
├── full-<시각>.<값>/         # ② K=64 (9)
├── full-<시각>.<값>/         # ③ K=8192 (9)
└── full-<시각>.<값>/         # ④ Seed 20260930 (9)
results-envB-diag/           # 5절을 했을 때만
```

각 `full-*` 폴더에는 `environment.txt`, `console.log`, `jmh.json`, `summary.csv`, `raw.csv`, `secondary.csv`가 있다.

### 6.2 보내기 전 확인

- [ ] 화면 마지막에 `전체 완료`가 출력되었다.
- [ ] `results-envB/system/system_info.txt`의 java 버전이 `25.0.4.1`이다.
- [ ] `results-envB/` 아래 `full-*` 폴더가 4개다.
- [ ] 주파수 정책과 perf 설정을 원래대로 되돌렸다(바꿨다면).

그림은 주저자가 Mac에서 만든다. 공동저자가 matplotlib을 설치할 필요는 없다.

---

## 7. 문제 해결

| 증상 | 원인과 해결 |
|---|---|
| `JDK가 25.0.4.1 이 아니다` | 2절의 PATH 설정을 확인한다. 새 터미널을 열고 `java -version`을 다시 본다 |
| `javac가 없다` | JRE만 잡혀 있다. `which javac`가 `~/jdk/jdk-25.0.4.1+1/bin/javac`인지 확인한다 |
| `정확성 검사가 48개 입력을 통과하지 못했다` | 코드가 바뀌었거나 압축이 손상되었다. 다시 받아 푼다. 계속 실패하면 `results-envB/system/check.log`를 주저자에게 보낸다 |
| `벤치마크 3개가 등록되지 않았다` | `results-envB/system/build.log`를 확인한다. `.deps/` 폴더에 jar 4개가 있어야 한다 |
| `summary.csv가 N줄이다(기대: M)` 또는 `console.log에 오류` | 해당 폴더의 `console.log`를 주저자에게 보낸다. 임의로 다시 돌리지 않는다 |
| `perf를 쓸 수 없어 건너뛴다` | 5절 준비가 안 된 것이다. 선택 항목이라 그대로 두어도 된다 |
| 측정 중 절전·재부팅·강제 종료 | 중단된 실행은 불완전하다. `results-envB`를 `results-envB-중단`으로 이름을 바꾸고 4.2부터 다시 실행한다 |
| `python3가 없어 CSV가 만들어지지 않는다` | `sudo apt install python3`. 이미 끝난 측정은 `jmh.json`이 있으므로 주저자가 변환할 수 있다 |

---

## 8. 하지 말 것

- 코드, 스크립트, JMH 설정(반복 횟수, 병렬성, 힙)을 바꾸지 않는다. 환경 A와 조건이 달라진다.
- 다른 JDK로 돌린 결과를 섞지 않는다.
- 측정 중 컴퓨터를 쓰지 않는다. 브라우저 하나도 결과를 흔든다.
- 배터리로 돌리지 않는다.
- `results-envB/` 안의 파일을 고치거나 지우지 않는다.

---

## 9. 참고

- 실험 조건과 용어의 정의: `실험과정및정의내역.md`
- 환경 A의 결과와 해석: `결과분석표.md`
- 스크립트 옵션: `run_envB.sh` 맨 위의 주석
  - `PIN=0`: 코어 고정 끔
  - `SKIP_DIAG=1`: perf 단계 생략
  - `ALLOW_WRONG_JDK=1`: 다른 JDK 허용(논문용 아님)
- 단계만 따로 실행: `bash run_envB.sh preflight` (`check`, `build`, `main`, `diag`, `pack`도 가능)
