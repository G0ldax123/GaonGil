from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.data_loader import BASE_DIR
from backend.route_service import build_recommendation


app = FastAPI(title="GaonGil API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")


class RecommendRequest(BaseModel):
    start: str
    end: str
    userType: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/recommend")
def recommend(request: RecommendRequest) -> dict:
    result = build_recommendation(
        start=request.start,
        end=request.end,
        user_type=request.userType,
    )

    if result is None:
        raise HTTPException(status_code=404, detail="Route set not found")

    return result
