# 알고리즘 제출 폴더

각 팀원은 이 폴더에 자신의 DNA 복원 알고리즘 Python 파일을 하나씩 추가합니다.

예시:

```text
algorithms/
  template.py
  minsu.py
  jiyoon.py
  seoyeon.py
  hyunwoo.py
```

## 제출 규격

각 알고리즘 파일에는 반드시 아래 함수가 있어야 합니다.

```python
def reconstruct(reads, reference_length, metadata):
    """복원한 DNA 문자열을 반환합니다."""
    return ""
```

입력값:

- `reads`: 시뮬레이션된 DNA read 문자열 리스트
- `reference_length`: 원본 reference DNA 문자열 길이
- `metadata`: 실험 조건 정보가 들어 있는 dictionary

`metadata`에 들어 있는 값:

- `alphabet`: 사용 문자, 기본값은 `"ATCG"`
- `seed`: 랜덤 seed
- `read_length`: read 길이
- `read_count`: 생성된 read 개수
- `coverage`: coverage 값
- `noise_rate`: 염기 치환 noise 비율
- `reference_length`: 원본 reference 길이

## 작성 방법

1. `template.py`를 복사해서 자신의 이름으로 파일을 만듭니다.
2. `reconstruct(...)` 함수 안에 알고리즘을 구현합니다.
3. 복원한 DNA 문자열을 `str`로 반환합니다.

예시:

```python
def reconstruct(reads, reference_length, metadata):
    joined = "".join(reads)
    return joined[:reference_length]
```

위 예시는 좋은 알고리즘이 아니라 함수 형식을 보여주기 위한 예시입니다.

## 평가에서 제외되는 파일

아래 파일은 benchmark runner가 실행하지 않습니다.

- `template.py`
- `_helper.py`처럼 `_`로 시작하는 파일

공통 helper 함수가 필요하면 `_utils.py`처럼 `_`로 시작하는 파일에 둘 수 있습니다.

## 포함된 예시 알고리즘

이 폴더에는 형식 참고용 예시 알고리즘도 들어 있습니다.

- `denovo_greedy.py`: read 사이의 suffix-prefix overlap을 이용해 de novo 방식으로 contig를 만드는 간단한 알고리즘
- `bwt_overlap.py`: BWT 기반 k-mer index로 read 우선순위를 정한 뒤 greedy overlap assembly를 수행하는 예시
- `position_table_mapping.py`: 허용 mismatch가 `e`개일 때 read를 `e + 1`개 구간으로 나누고, 적어도 한 구간은 exact match된다는 pigeonhole principle을 이용하는 position table mapping 예시

이 예시들은 수업용 baseline/reference 구현입니다. 성능이 좋은 최종 알고리즘이라는 뜻은 아닙니다.

## 주의사항

- 함수 이름은 반드시 `reconstruct`여야 합니다.
- 반환값은 반드시 문자열이어야 합니다.
- 함수 안에서 `input()`을 호출하지 마세요.
- 파일을 직접 읽거나 쓰지 않는 것을 권장합니다.
- 너무 오래 실행되면 timeout으로 기록됩니다.
- crash나 exception이 발생하면 해당 실험 row에 실패로 기록됩니다.
