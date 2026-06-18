# C++ 알고리즘 제출 폴더

팀원 알고리즘은 `algorithms/` 폴더에 C++ 파일 하나로 제출합니다. 벤치마크는 `template.cpp`와 `_`로 시작하는 파일을 제외한 `*.cpp` 파일을 자동으로 컴파일하고 실행합니다.

```text
algorithms/
  template.cpp
  kmp_exact_match.cpp
  BWT.cpp
  suffixarray.cpp
  table_search.cpp
```

## 컴파일 방식

Python 벤치마크가 각 C++ 파일을 다음 방식으로 컴파일합니다.

```text
g++ -std=c++17 -O2 algorithms/파일명.cpp -o 실행파일
```

## 입력 데이터 포맷

각 알고리즘 실행 파일은 표준입력으로 데이터를 받습니다. 실제 입력 순서는 다음과 같습니다.

```text
reference_length
reference
read_count
read_1
read_2
...
read_{read_count}
metadata_count
key=value
key=value
...
```

각 항목의 의미는 다음과 같습니다.

| 항목 | 의미 |
|---|---|
| `reference_length` | 레퍼런스 서열 길이 |
| `reference` | 알고리즘이 read를 매칭할 레퍼런스 서열 |
| `read_count` | 입력 read 개수 |
| `read_i` | 생성 유전체에서 추출된 read |
| `metadata_count` | 뒤따르는 `key=value` 줄 개수 |
| `key=value` | 실험 조건 정보 |

예시 입력은 다음과 같습니다.

```text
20
ATCGATCGATCGATCGATCG
3
ATCGAT
CGATCG
GATCGA
10
allowed_mismatches=2
alphabet=ATCG
coverage=2.0
genome_length=20
genome_mutation_rate=0.01
noise_rate=0.001
read_count=3
read_length=6
reference_length=20
seed=1
```

주요 metadata key는 다음과 같습니다.

| key | 의미 |
|---|---|
| `allowed_mismatches` | read 배치 시 허용할 mismatch 개수 |
| `alphabet` | 사용하는 염기 문자 |
| `seed` | 데이터 생성에 사용한 난수 seed |
| `reference_path` | 레퍼런스 파일 경로 |
| `reference_start` | 레퍼런스에서 잘라낸 시작 위치 |
| `reference_length` | 레퍼런스 서열 길이 |
| `genome_length` | 생성 유전체 길이 |
| `genome_mutation_rate` | 생성 유전체를 만들 때 적용한 변이 비율 |
| `read_length` | read 길이 |
| `read_count` | read 개수 |
| `coverage` | 평균 read coverage |
| `noise_rate` | read 생성 시 적용한 오류 비율 |

## 출력 데이터 포맷

표준출력에는 재구성한 DNA 서열만 출력합니다.

```text
ATCGATCG...
```

로그나 디버그 메시지가 필요하면 표준출력이 아니라 표준에러를 사용합니다.

```cpp
cerr << "debug message\n";
```

## 주의사항

- 알고리즘은 정답 유전체 서열을 입력으로 받지 않습니다.
- 알고리즘은 레퍼런스와 read만 보고 재구성 서열을 출력해야 합니다.
- 출력 서열 길이는 `reference_length`에 맞추는 것을 권장합니다.
- 컴파일 오류, 실행 중 crash, timeout은 결과 CSV에 실패 row로 기록됩니다.
