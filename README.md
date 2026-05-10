# 26_2_Algorithm_team5

DNA 문자열 복원 알고리즘 성능 평가 환경입니다.

팀원들은 `algorithms/` 폴더에 정해진 형식의 Python 알고리즘 파일만 추가하면 됩니다. 이후 benchmark runner가 같은 조건에서 각 알고리즘을 실행하고, 성능 결과 CSV와 시각화 PNG, HTML 리포트를 자동으로 생성합니다.

## 1. 가상환경 설정

처음 한 번만 실행합니다.

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

이미 가상환경을 만든 뒤라면 작업할 때마다 활성화만 하면 됩니다.

```powershell
.venv\Scripts\Activate.ps1
```

## 2. 알고리즘 제출 방법

각 팀원은 `algorithms/` 폴더 안에 자신의 Python 파일을 하나 추가합니다.

예시:

```text
algorithms/
  template.py
  minsu.py
  jiyoon.py
  ...
```

파일 안에는 반드시 아래 함수를 정의해야 합니다.

```python
def reconstruct(reads, reference_length, metadata):
    """복원한 DNA 문자열을 반환합니다."""
    return ""
```

입력값:

- `reads`: 시뮬레이션된 DNA read 문자열 리스트
- `reference_length`: 원본 reference DNA 문자열 길이
- `metadata`: 실험 조건 정보가 들어 있는 dictionary

`metadata`에는 다음 값들이 들어 있습니다.

- `alphabet`: 사용 문자, 기본값은 `"ATCG"`
- `seed`: 랜덤 seed
- `read_length`: read 길이
- `read_count`: 생성된 read 개수
- `coverage`: coverage 값
- `noise_rate`: 염기 치환 noise 비율
- `reference_length`: 원본 reference 길이

주의:

- 함수는 반드시 `str`을 반환해야 합니다.
- `template.py`와 `_`로 시작하는 파일은 평가에서 제외됩니다.
- 팀원 알고리즘 구현 파일 외의 benchmark 코드는 특별한 이유 없이 수정하지 마세요.

## 3. 빠른 실행 테스트

전체 실험 전에 먼저 작은 설정으로 평가 환경이 정상 동작하는지 확인합니다.

```powershell
python -m benchmark.run --quick --out results/quick
```

성공하면 아래 파일들이 생성됩니다.

```text
results/quick/results.csv
results/quick/report.html
results/quick/figures/*.png
```

## 4. 기본 전체 실험 실행

기본 설정 파일은 `configs/default.yaml`입니다.

```powershell
python -m benchmark.run --config configs/default.yaml --out results/latest
```

실험 조건은 기본적으로 다음 변수를 조절합니다.

- reference 길이
- read 길이
- coverage
- noise 비율
- random seed

각 알고리즘은 같은 조건에서 실행되며, crash나 timeout이 발생해도 전체 benchmark는 멈추지 않고 결과 CSV에 기록됩니다.

## 5. 결과물 확인

실험 결과는 지정한 `results/<run-name>/` 폴더에 저장됩니다.

```text
results/latest/results.csv
results/latest/report.html
results/latest/figures/
```

주요 결과:

- `results.csv`: 모든 실험 결과 원본 데이터
- `report.html`: 요약 표와 그래프를 포함한 HTML 리포트
- `figures/*.png`: 보고서나 발표자료에 넣을 수 있는 고해상도 그래프

측정 지표:

- 실행 시간
- 복원 정확도
- edit distance
- 복원 문자열 길이 비율
- crash/timeout 여부
- 가능한 경우 peak memory

## 6. 기존 결과 CSV로 리포트 다시 만들기

이미 생성된 CSV로 그래프와 HTML 리포트만 다시 만들 수 있습니다.

```powershell
python -m benchmark.report --results results/latest/results.csv --out results/latest
```

## 7. 테스트 실행

benchmark 코드가 정상인지 확인하려면 다음을 실행합니다.

```powershell
python -m pytest
python -m benchmark.run --quick --out results/quick
```

## 8. 폴더 구조

```text
algorithms/              팀원 알고리즘 제출 폴더
benchmark/               평가 환경 코드
configs/default.yaml     기본 실험 설정
results/                 실행 결과 저장 폴더
tests/                   평가 환경 테스트
requirements.txt         Python 의존성 목록
```
