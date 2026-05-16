# GaonGil AI

`ai/`는 가온길 MVP의 route 단위 접근성 분석 모듈입니다.

역할은 경로를 직접 생성하는 것이 아니라, 백엔드가 넘긴 route 후보와 각 point의 로드뷰 이미지를 AI 모델에 전달해서 `data/ai_results.json`과 호환되는 분석 결과를 만드는 것입니다.

## 처리 흐름

1. `data/routes.json`에서 route 후보를 읽습니다.
2. route의 각 point에 연결된 `assets/roadview/...` 이미지를 찾습니다.
3. route 하나 전체를 `ai/prompt.md`와 함께 AI 모델에 전달합니다.
4. AI가 route 요약과 point별 위험 요소를 JSON으로 반환합니다.
5. 결과를 `data/ai_results.json`에 저장합니다.

백엔드에서 `/recommend` 요청을 처리할 때도 이 흐름을 사용합니다.

## 주요 파일

```text
ai/prompt.md            # 접근성 판단 기준과 출력 JSON 형식
ai/src/analyzer.py      # OpenAI/Gemini API 호출
ai/src/route_ranker.py  # route 분석, 정렬, 결과 정규화
ai/src/main.py          # 로컬 실행용 CLI
ai/requirements.txt     # AI 파트 Python 의존성
```

## 지원 사용자 유형

- `wheelchair`: 휠체어 이용자
- `stroller`: 유모차 이용자
- `elderly`: 노약자
- `crutches`: 목발 이용자

AI 결과는 요청으로 들어온 `userType`을 기준으로 정규화됩니다. 모델이 잘못된 `userTypeLabel`을 반환해도 `route_ranker.py`에서 요청값 기준으로 보정합니다.

## 환경 변수

루트 `.env` 또는 셸 환경 변수로 설정합니다.

```bash
AI_ANALYZER_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-5.4
```

Gemini를 사용할 경우:

```bash
AI_ANALYZER_PROVIDER=google
GOOGLE_API_KEY=your_key
GOOGLE_MODEL=gemini-2.0-flash
```

## CLI 실행

저장소 루트에서 실행합니다.

```bash
cd /home/user/GaonGil
source .venv/bin/activate
python -m ai.src.main --user-type wheelchair
```

특정 route만 분석:

```bash
python -m ai.src.main --user-type crutches --route-id route_a
```

출발지/도착지를 직접 지정:

```bash
python -m ai.src.main \
  --user-type stroller \
  --origin 메디트 \
  --destination 드림하우스
```

출력 파일 지정:

```bash
python -m ai.src.main --user-type elderly --output /tmp/ai_results.json
```

`--output`을 생략하면 기본적으로 `data/ai_results.json`에 저장합니다. `--route-id`를 지정하면 기존 결과에서 같은 `(routeId, userType)` 조합만 교체합니다.

## 출력 형식

AI는 route별로 아래 형태의 JSON을 반환해야 합니다.

```json
{
  "routeId": "route_a",
  "userType": "crutches",
  "userTypeLabel": "목발 이용자",
  "routeSummary": {
    "recommendation": "안전 | 주의 | 위험",
    "summaryTitle": "짧은 제목",
    "aiSummary": "짧은 한 문장 요약",
    "mainRiskFactors": ["계단", "단차", "경사로", "좁은 길"],
    "mainRiskPoints": ["a_1: 경사로"],
    "reason": "판단 근거"
  },
  "points": [
    {
      "pointId": "a_1",
      "locationName": "경로 A 주요 지점 1",
      "detectedElements": {
        "stairs": "false",
        "curb": "false",
        "steepRoad": "true",
        "narrowRoad": "false"
      },
      "recommendation": "주의",
      "summaryTitle": "경사로 주의",
      "aiSummary": "경사로로 주의가 필요합니다.",
      "reason": "실제 이동 경로에 부담되는 경사로가 보입니다."
    }
  ]
}
```

정확한 예시는 `docs/ai_results.json`과 `data/ai_results.json`을 참고합니다.

## 판단 기준

판단 기준은 코드가 아니라 `ai/prompt.md`에 둡니다.

현재 주요 위험 요소는 네 가지입니다.

- `계단`
- `단차`
- `경사로`
- `좁은 길`

`경사로`는 일반적인 오르막/내리막이 아니라, 실제 이동 경로에서 통행 부담을 만드는 경사일 때만 위험 요소로 사용합니다. 단, `steepRoad`가 `"true"`이면 point 추천은 최소 `"주의"`가 되도록 프롬프트에 명시되어 있습니다.

## 백엔드 연동

백엔드는 `backend.ai_service.generate_ai_results()`를 통해 AI 분석을 실행합니다.

```python
from backend.ai_service import generate_ai_results

results = generate_ai_results(
    route_payloads=routes,
    user_type="crutches",
)
```

최종 `/recommend` 응답은 `backend.route_service.build_recommendation()`에서 route 데이터와 AI 결과를 병합해 만듭니다.
