# 가온길 - AI Hack Camp 2026 우수상

AI 기반 교통약자 맞춤형 경로 안내 MVP입니다.

프론트에서 사용자 유형, 출발지, 도착지를 선택하면 백엔드가 미리 준비된 route 데이터를 구성하고, route 단위로 AI 분석을 실행한 뒤 프론트가 바로 표시할 수 있는 추천 결과를 반환합니다.

## 주요 흐름

1. 프론트엔드가 `POST /recommend`로 `{ start, end, userType }`을 보냅니다.
2. 백엔드가 `data/routes.json`의 route/point 정보와 로드뷰 이미지 경로를 읽습니다.
3. AI 모듈이 route 단위로 `ai/prompt.md`와 로드뷰 이미지를 모델에 전달합니다.
4. AI 결과를 `data/ai_results.json`에 저장합니다.
5. 백엔드가 route 정보와 AI 결과를 병합해서 프론트에 반환합니다.

## 디렉터리 구조

```text
ai/        # route 단위 AI 분석 코드와 프롬프트
assets/    # route별 로드뷰 이미지
backend/   # FastAPI 서버와 추천 API
data/      # 실제 실행에 쓰는 routes/ai_results/front_request 데이터
docs/      # 예시 JSON과 API 응답 문서
frontend/  # Figma export 기반 프론트 프로토타입 서버
```

## 환경 변수

루트의 `.env`에 API 키와 모델 설정을 둡니다. `.env`는 Git에 올리지 않습니다.

```bash
AI_ANALYZER_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-5.4

# Gemini 사용 시
GOOGLE_API_KEY=your_key
GOOGLE_MODEL=gemini-2.0-flash
```

`AI_ANALYZER_PROVIDER`는 `openai` 또는 `google`을 사용합니다.

## 백엔드 실행

```bash
cd /home/user/GaonGil
source .venv/bin/activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

확인:

```bash
curl http://127.0.0.1:8000/health
```

## 프론트엔드 실행

```bash
cd /home/user/GaonGil
node frontend/app.js
```

접속:

```text
http://127.0.0.1:5173/
```

## API

### `GET /health`

서버 상태 확인용 API입니다.

```json
{
  "status": "ok"
}
```

### `POST /recommend`

요청:

```json
{
  "start": "메디트",
  "end": "드림하우스",
  "userType": "crutches"
}
```

지원하는 `userType`:

- `wheelchair`: 휠체어 이용자
- `stroller`: 유모차 이용자
- `elderly`: 노약자
- `crutches`: 목발 이용자

응답은 모든 route 후보를 한 번에 반환합니다. 각 route에는 추천 상태, 요약, 주요 위험 요소, 위험 지점, point별 분석 결과가 포함됩니다.

## 데이터 파일

- `data/routes.json`: 후보 route와 point, 로드뷰 이미지 경로
- `data/ai_results.json`: AI 분석 결과 저장 파일
- `data/front_request.json`: CLI/테스트용 기본 요청 예시
- `data/coordinate.json`: 프론트 지도 위 위험 아이콘 좌표
