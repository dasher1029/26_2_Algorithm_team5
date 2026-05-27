# 26_2_Algorithm_team5

DNA 문자열 복원 알고리즘 성능 평가 하네스입니다.

이 프로젝트는 교수님 피드백에 맞춰 외부 데이터에서는 reference genome txt만 가져오고, 실험용 `my genome`과 reads는 하네스 안에서 직접 생성합니다. 팀원 알고리즘은 C++로 작성하고, Python benchmark runner가 같은 reads로 컴파일/실행/평가/그래프 생성을 담당합니다. 결과는 gold standard인 `my genome`과 비교되며, 내장 `trivial_concat` baseline도 항상 같이 실행됩니다.

## 1. 환경 설정

팀 공통 실행은 **Docker 사용을 권장**합니다. Docker 이미지는 Python 3.9, `g++`, Python 패키지를 모두 포함하므로 각자 컴퓨터에 Python이나 C++ 컴파일러를 따로 맞출 필요가 없습니다. Windows에서는 Docker Desktop을 먼저 실행해 둬야 합니다.

처음 한 번 이미지를 빌드합니다.

```powershell
docker compose build
```

테스트 실행:

```powershell
docker compose run --rm benchmark python -m pytest
```

빠른 benchmark 실행:

```powershell
docker compose run --rm benchmark python -m benchmark.run --quick --out results/quick
```

전체 benchmark 실행:

```powershell
docker compose run --rm benchmark python -m benchmark.run --config configs/default.yaml --out results/latest
```

로컬 가상환경은 Docker를 쓰지 않을 때만 사용합니다. 이 경우 Python 3.9와 `g++`가 각자 컴퓨터에 설치되어 있어야 합니다.

Windows PowerShell:

```powershell
py -3.9 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

이미 가상환경을 만든 뒤라면 작업할 때마다 활성화만 하면 됩니다.

```powershell
.\.venv\Scripts\Activate.ps1
```

## 2. 실험 데이터 흐름

하네스는 다음 순서로 입력을 만듭니다.

```text
reference txt
  -> configs/default.yaml의 reference_start/genome_length로 구간 선택
  -> genome_mutation_rate와 seed로 my genome 생성
  -> my genome에서 reads 생성
  -> trivial baseline과 팀원 알고리즘 실행
  -> my genome(gold standard)과 reconstruction 비교
```

reference txt는 plain txt든 FASTA 형태든 파일 안의 `A/T/C/G` 문자만 대문자로 추출해서 사용합니다.

## 3. 설정 파일

기본 설정은 `configs/default.yaml`입니다.

```yaml
experiment:
  alphabet: "ATCG"
  reference_path: "data/example_reference.txt"
  reference_starts: [0]
  genome_lengths: [500, 1000]
  genome_mutation_rates: [0.0]
  read_lengths: [30, 45]
  coverages: [3]
  noise_rates: [0.001]
  seeds: [1]
  timeout_seconds: 10
```

실제 reference genome txt를 쓰려면 `reference_path`만 원하는 파일 경로로 바꾸면 됩니다. 큰 reference 파일은 레포에 커밋하지 말고 로컬 파일로 두는 것을 권장합니다.

## 4. 알고리즘 제출 방법

각 팀원은 `algorithms/` 폴더에 C++ 파일 하나를 추가합니다.

```text
algorithms/
  template.cpp
  minsu.cpp
  jiyoon.cpp
  seoyeon.cpp
  hyunwoo.cpp
```

Python runner는 `*.cpp` 파일을 `g++ -std=c++17 -O2`로 컴파일한 뒤 실행합니다. `template.cpp`와 `_`로 시작하는 helper 파일은 benchmark 대상에서 제외됩니다.

알고리즘 실행 파일은 stdin에서 아래 형식으로 입력을 받습니다.

```text
reference_length
reference
read_count
read_1
read_2
...
read_N
metadata_count
key=value
key=value
...
```

입력값:

- `reads`: 하네스가 생성한 read 문자열 리스트
- `reference`: mutation 전 reference slice 문자열
- `reference_length`: gold standard인 `my genome` 길이
- `metadata`: 실험 조건 dictionary

`metadata`에는 다음 값들이 들어갑니다.

- `alphabet`
- `seed`
- `reference_path`
- `reference_start`
- `genome_length`
- `genome_mutation_rate`
- `read_length`
- `read_count`
- `coverage`
- `noise_rate`
- `reference_length`

주의:

- 알고리즘에는 gold standard 문자열이 직접 전달되지 않습니다.
- 알고리즘은 reference와 reads를 이용해 my genome을 추정하고, 추정 결과를 stdout에 출력합니다.
- stdout에는 복원한 DNA 문자열만 출력해야 합니다.
- crash와 timeout은 전체 실행을 멈추지 않고 결과 CSV에 실패 row로 기록됩니다.

## 5. 빠른 검증

작은 설정으로 하네스가 정상 동작하는지 확인합니다.

```powershell
docker compose run --rm benchmark python -m benchmark.run --quick --out results/quick
```

생성되는 파일:

```text
results/quick/results.csv
results/quick/report.html
results/quick/figures/*.png
```

## 6. 전체 실험 실행

```powershell
docker compose run --rm benchmark python -m benchmark.run --config configs/default.yaml --out results/latest
```

결과 CSV에는 알고리즘 이름, 상태, runtime, accuracy, edit distance, reference 경로/구간, genome mutation rate, read 조건, seed, crash/timeout 정보가 기록됩니다.

## 7. 리포트 재생성

이미 생성된 CSV로 그래프와 HTML 리포트만 다시 만들 수 있습니다.

```powershell
docker compose run --rm benchmark python -m benchmark.report --results results/latest/results.csv --out results/latest
```

## 8. 테스트

```powershell
docker compose run --rm benchmark python -m pytest
```

권장 검증 순서:

```powershell
docker compose run --rm benchmark python -m pytest
docker compose run --rm benchmark python -m benchmark.run --quick --out results/quick
```
