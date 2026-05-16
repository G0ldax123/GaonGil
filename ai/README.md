# AI/Data MVP

가온길의 AI/데이터 파트는 `docs/routes.json`의 route/point 정보를 읽고, 로드뷰 이미지를 기준으로 접근성 분석 결과 JSON을 생성한다.

## 역할

- static route data 로드
- 로드뷰 이미지 경로 매핑
- `ai/prompt.md` 기반 Google Gemini 이미지 분석
- API 키가 없거나 실패하면 mock analyzer fallback
- point 위험도 계산
- route 위험도 집계 및 추천 순위 산출
- 프론트/백엔드가 바로 쓰는 JSON 출력

## 파이프라인

1. `docs/routes.json`이 있으면 그 파일을 우선 읽고, 없으면 `ai/data/routes_seed.json`을 fallback으로 읽는다.
2. 입력 `routes[].points[]`를 point 단위로 분석하고, 각 지점의 `slopePercent`, `imageUrl`, `mockDetected`를 불러온다.
3. `GOOGLE_API_KEY`가 있으면 Gemini REST API로 이미지와 `ai/prompt.md`를 보내 JSON 분석 결과를 받는다.
4. API 키가 없거나 호출이 실패하면 `MockAccessibilityAnalyzer`가 fallback 분석을 수행한다.
5. 규칙 기반 점수 계산기로 user type 별 point risk score를 계산한다.
6. route 단위로 점수를 합산하고 `routeSummary`를 만든다.
7. 최종 결과를 `docs/ai_results.json` 형태의 route 리스트로 stdout 또는 함수 반환값으로 제공한다.

## 실행 방법

저장소 루트에서:

```bash
cd /home/ubuntu/GaonGil
nvm use
source ai/.venv/bin/activate
python -m ai.src.main --user-type wheelchair
```

Google Gemini를 쓰려면:

```bash
export GOOGLE_API_KEY=your_key
export AI_ANALYZER_PROVIDER=google
python -m ai.src.main --user-type wheelchair
```

특정 route만 테스트하려면:

```bash
python -m ai.src.main --user-type wheelchair --route-id route_a
```

또는:

```bash
cd /home/ubuntu/GaonGil/ai
source .venv/bin/activate
python src/main.py --user-type wheelchair
```

## Input Data 구조

`docs/routes.json` 구조:

- `routeSetId`
- `start.name`, `end.name`
- `routes[]`
- `routeId`, `name`, `description`, `duration`, `distance`
- `points[]`
- `pointId`, `locationName`, `lat`, `lng`
- `imageUrl`, `slopePercent`, `slopeLevel`

주의:

- 로컬 자산은 `assets/roadview/<route_id>/route_a_*.jpg`처럼 route 하위 폴더로 관리한다.
- 입력 JSON의 `imageUrl`과 동일한 stem의 `.jpg`, `.jpeg`, `.png` 자산을 순서대로 매핑한다.

## 최종 출력 JSON 예시

최종 스키마 예시는 [docs/ai_results.json](/home/ubuntu/GaonGil/docs/ai_results.json:1)에 있다.

주요 필드:

- `routeId`
- `userType`
- `userTypeLabel`
- `routeSummary`
- `routeSummary.recommendation`
- `routeSummary.riskLevel`
- `routeSummary.aiSummary`
- `points[]`
- `points[].detectedElements`
- `points[].riskFactors[]`
- `points[].aiSummary`

## 백엔드/프론트 연동

백엔드가 Python이면 다음 함수를 직접 호출하면 된다.

```python
from ai.src.route_ranker import analyze_routes_for_user

payload = analyze_routes_for_user(
    user_type="wheelchair",
    origin="고려대학교",
    destination="안암역",
)
```

Node.js 백엔드 또는 프론트 시연에서는 CLI 결과 JSON을 읽으면 된다.

```bash
python -m ai.src.main --user-type stroller > ai_result.json
```

## 향후 TODO

- 실제 Google/Gemini 응답을 기반으로 prompt 튜닝
- route_b, route_c 지점/이미지 추가
- 로드뷰 이미지와 point 설명 동기화
- 커뮤니티 제보 데이터 반영
- 지하철 엘리베이터 실시간 운행 상태 반영
