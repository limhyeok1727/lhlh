# sample-project — 웹 액세스 로그 트래픽 리포트

웹 액세스 로그를 요약해서 일일 트래픽 리포트(텍스트)를 만드는 2단계 파이프라인입니다.

- **기술 스택**: Python 3.9+ (표준 라이브러리만 사용, 외부 의존성 없음)
- 코드 컨벤션, 아키텍처, Git 규칙 등 상세 가이드는 [CLAUDE.md](./CLAUDE.md) 참고

## 구성

```
src/
  log_parser.py   # 로그 파일을 읽어 통계 dict로 요약
  report.py       # 통계 dict를 텍스트 리포트로 렌더링
tests/
  test_top_endpoint_by_status.py
data/
  access_2026-07-15.log   # 데모/테스트용 샘플 로그
```

## 이번에 추가한 기능: 상태코드별 최다 엔드포인트

`log_parser.summarize()`가 상태 버킷(2xx/3xx/4xx/5xx)별로 가장 많이 호출된
엔드포인트를 함께 집계합니다(`top_endpoint_by_status` 키, 빈 버킷은 `None`).
`report.py`는 이를 "TOP ENDPOINT BY STATUS" 섹션으로 렌더링해 리포트에
포함합니다. 어떤 엔드포인트가 실패(5xx)나 느린 응답에 몰려 있는지 리포트에서
바로 확인할 수 있습니다.

기존 반환 키(`total`, `2xx`, `top_endpoints` 등)와 함수 시그니처는 그대로
유지했습니다(하위 호환).

## 실행 방법

### 로그 요약

```
python src/log_parser.py data/access_2026-07-15.log
```

출력 예시:

```
total requests : 31
2xx / 3xx      : 21 / 2
4xx / 5xx      : 4 / 4
avg latency    : 311ms
top endpoints  :
  /api/orders  16
  /api/products  7
  /api/login  2
top endpoint by status:
  2xx: /api/orders  (12)
  3xx: /legacy/export  (2)
  4xx: /api/users/42  (1)
  5xx: /api/orders  (4)
```

### 리포트 생성

```
python src/report.py
```

(현재 `__main__` 블록은 하드코딩된 샘플 dict를 렌더링합니다. 실제 로그와
연결하려면 `report.make(log_parser.summarize(path))` 형태로 직접 호출해야
합니다.)

출력 예시:

```
========================================
 DAILY TRAFFIC REPORT
========================================
 generated: 2026-07-21
----------------------------------------
 total     : 31
 success   : 21 (67.7%)
 redirect  : 2 (6.5%)
 client err: 4 (12.9%)
 server err: 4 (12.9%)
----------------------------------------
 ALERTS
----------------------------------------
 [!] server error rate over 5% - check on-call
 [!] avg latency over 300ms - check slow queries
----------------------------------------
 TOP ENDPOINT BY STATUS
----------------------------------------
 2xx : /api/orders  (12)
 3xx : /legacy/export  (2)
 4xx : /api/users/42  (2)
 5xx : /api/orders  (4)
----------------------------------------
 TOP ENDPOINTS
----------------------------------------
 /api/orders  16
 /api/products  7
 /api/login  2
========================================
```

## 테스트

pytest가 설치되어 있지 않은 환경이라 표준 라이브러리 `unittest`로 작성했습니다.

```
python -m unittest discover -s tests -v
```

### 실행 결과

```
test_empty_bucket_is_none (test_top_endpoint_by_status.TopEndpointByStatusTest.test_empty_bucket_is_none) ... ok
test_most_frequent_endpoint_wins_in_bucket (test_top_endpoint_by_status.TopEndpointByStatusTest.test_most_frequent_endpoint_wins_in_bucket) ... ok
test_report_renders_new_and_existing_sections (test_top_endpoint_by_status.TopEndpointByStatusTest.test_report_renders_new_and_existing_sections) ... ok
test_short_lines_are_skipped (test_top_endpoint_by_status.TopEndpointByStatusTest.test_short_lines_are_skipped) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.040s

OK
```

4건 모두 통과: (a) 버킷 내 최다 엔드포인트 선택, (b) 빈 버킷 `None` 처리,
(c) 리포트 렌더링(신규 섹션 + 기존 섹션 회귀 확인), (d) 필드 수 부족한
줄 스킵.
