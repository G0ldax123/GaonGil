# AI/Data MVP

가온길의 AI 파트는 `data/routes.json`의 route/point 정보를 읽고, route 단위로 `ai/prompt.md`와 로드뷰 이미지를 AI 모델에 전달해서 `data/ai_results.json` 형태의 분석 결과를 생성한다.

## 역할

- route data 로드
- 로드뷰 이미지 경로 매핑
- `ai/prompt.md` 기반 route 단위 이미지 분석
- OpenAI 또는 Google Gemini API 호출
- 프론트/백엔드가 바로 쓰는 `ai_results.json` 출력

## 파이프라인

1. `data/routes.json`을 우선 읽고, 없으면 `docs/routes.json`을 읽는다.
2. 각 route의 point 목록과 `assets/roadview/<route_id>/` 이미지를 매핑한다.
3. route 하나당 `ai/prompt.md`, route metadata, route 이미지 전체를 한 번에 AI 모델로 보낸다.
4. AI 모델이 `ai_results.json`과 호환되는 route JSON 하나를 반환한다.
5. CLI가 route 결과들을 합쳐 `data/ai_results.json`에 저장한다.

## 실행 방법

저장소 루트에서:

```bash
cd /home/user/GaonGil
nvm use
source .venv/bin/activate
python -m ai.src.main --user-type wheelchair
```

Google Gemini를 쓰려면:

```bash
export GOOGLE_API_KEY=your_key
export AI_ANALYZER_PROVIDER=google
python -m ai.src.main --user-type wheelchair
```

OpenAI GPT 모델을 쓰려면:

```bash
export OPENAI_API_KEY=your_key
export OPENAI_MODEL=gpt-5.4
export AI_ANALYZER_PROVIDER=openai
python -m ai.src.main --user-type wheelchair --route-id route_b
```

특정 route만 테스트하려면:

```bash
python -m ai.src.main --user-type wheelchair --route-id route_a
```

또는:

```bash
cd /home/user/GaonGil/ai
source ../.venv/bin/activate
python src/main.py --user-type wheelchair
```

## Input Data 구조

`data/routes.json` 구조:

- `routeSetId`
- `userType`
- `start.name`, `end.name`
- `routes[]`
- `routeId`, `name`, `description`
- `points[]`
- `pointId`, `locationName`
- `imageUrl`

주의:

- 로컬 자산은 `assets/roadview/<route_id>/route_a_*.jpg`처럼 route 하위 폴더로 관리한다.
- 입력 JSON의 `imageUrl`과 동일한 stem의 `.jpg`, `.jpeg`, `.png` 자산을 순서대로 매핑한다.

## 최종 출력 JSON 예시

최종 스키마 예시는 `docs/ai_results.json`에 있다.

주요 필드:

- `routeId`
- `userType`
- `userTypeLabel`
- `routeSummary`
- `routeSummary.recommendation`
- `routeSummary.aiSummary`
- `routeSummary.mainRiskFactors`
- `routeSummary.mainRiskPoints`
- `points[]`
- `points[].detectedElements`
- `points[].recommendation`
- `points[].aiSummary`

## 백엔드/프론트 연동

백엔드 또는 로컬 스크립트에서 직접 호출할 수도 있다.

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

## 현재 범위

- Python 코드는 접근성 판단 룰을 직접 계산하지 않는다.
- 계단/단차/가파른 길/좁은 길 판단 기준은 `ai/prompt.md`에 고정한다.
- 코드의 역할은 route 로드, 이미지 첨부, AI 호출, 결과 저장으로 제한한다.
