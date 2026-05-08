from __future__ import annotations

from functools import lru_cache
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import strategies
from app.recommender import RecommenderService


class RecommendRequest(BaseModel):
    text: str = Field(..., min_length=1)
    strategy: str = "comfort"
    strength: float = Field(0.5, ge=0.0, le=1.0)
    top_k: int = Field(5, ge=1, le=20)


app = FastAPI(
    title="EMMR API",
    description="Emotion-regulation music recommendation backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def get_recommender() -> RecommenderService:
    return RecommenderService()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/strategies")
def get_strategies() -> List[str]:
    return strategies


@app.post("/recommend")
def recommend(req: RecommendRequest):
    service = get_recommender()

    return service.recommend(
        text=req.text,
        strategy=req.strategy,
        strength=req.strength,
        top_k=req.top_k,
    )