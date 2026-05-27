# C++ 알고리즘 제출 폴더

팀원 알고리즘은 이 폴더에 C++ 파일 하나로 제출합니다.

```text
algorithms/
  template.cpp
  minsu.cpp
  jiyoon.cpp
  seoyeon.cpp
  hyunwoo.cpp
```

## 제출 규격

Python benchmark runner가 각 `*.cpp` 파일을 `g++ -std=c++17 -O2`로 컴파일한 뒤 실행합니다.

제외되는 파일:

- `template.cpp`
- `_helper.cpp`처럼 `_`로 시작하는 파일
- 기존 `*.py` 파일

## 입력 형식

알고리즘 실행 파일은 stdin에서 아래 순서로 입력을 받습니다.

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

주요 metadata key:

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

## 출력 형식

stdout에는 복원한 DNA 문자열만 출력합니다.

```text
ATCG...
```

로그나 디버그 메시지는 stdout에 출력하지 마세요. 필요하면 stderr를 사용하세요.

## 주의

- 알고리즘은 gold standard인 `my genome`을 직접 받지 않습니다.
- 알고리즘은 mutation 전 reference slice와 reads를 입력으로 받아 read를 reference에 매핑하고, 추정한 my genome 문자열을 출력합니다.
- 반환 문자열 길이가 gold standard와 달라도 benchmark는 edit distance 기반으로 평가합니다.
- compile error, crash, timeout은 결과 CSV에 실패 row로 기록됩니다.
