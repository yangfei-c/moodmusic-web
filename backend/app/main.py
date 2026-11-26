from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import recommendation_pool_size, strategies
from app.feedback import record_event
from app.recommender import RecommenderService
from app.session_store import SessionStore


class RecommendRequest(BaseModel):
    text: str = Field(..., min_length=1)
    strategy: str = "comfort"
    strength: float = Field(0.5, ge=0.0, le=1.0)


class PlaybackEventRequest(BaseModel):
    current_song_id: Optional[str] = None
    play_duration_seconds: float = Field(0.0, ge=0.0)
    repeat_count: int = Field(0, ge=0)


class FeedbackRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    song_id: str = Field(..., min_length=1)
    music_preference: int = Field(..., ge=1, le=5)
    regulation_effect: int = Field(..., ge=1, le=5)
    play_duration_seconds: float = Field(0.0, ge=0.0)
    skipped: bool = False
    repeat_count: int = Field(0, ge=0)


app = FastAPI(
    title="MoodMusic-Web API",
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


@lru_cache(maxsize=1)
def get_session_store() -> SessionStore:
    return SessionStore()


def public_track(track: dict) -> dict:
    return {
        "song_id": track["song_id"],
        "audio_url": track.get("audio_url", ""),
        "display_tags": track.get("display_tags", []),
    }


def build_explanation(track: dict, state: dict) -> str:
    strategy_label = {
        "comfort": "安慰",
        "calm": "平静",
        "energize": "激活",
        "maintain": "保持",
    }.get(state.get("strategy"), "调节")
    tags = track.get("display_tags") or state.get("selected_strategy_tags") or []
    tag_text = "、".join(str(tag) for tag in tags[:3]) if tags else "当前情绪目标"
    return f"这首音乐更贴近你的{strategy_label}目标，并匹配 {tag_text} 等特征。"


def recommendation_response(session_id: str, track: dict, state: dict) -> dict:
    store = get_session_store()
    return {
        "session_id": session_id,
        "track": public_track(track),
        "explanation": build_explanation(track, state),
        "has_next": store.has_next(session_id),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/strategies")
def get_strategies() -> List[str]:
    return strategies


@app.post("/recommend")
def recommend(req: RecommendRequest):
    service = get_recommender()
    store = get_session_store()

    try:
        result = service.recommend(
            text=req.text,
            strategy=req.strategy,
            strength=req.strength,
            top_k=recommendation_pool_size,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    session = store.create(result["recommendations"], result["state"])
    return recommendation_response(
        session_id=session.session_id,
        track=session.candidates[session.cursor],
        state=session.state,
    )


@app.post("/recommend/{session_id}/next")
def next_recommendation(session_id: str, req: PlaybackEventRequest):
    store = get_session_store()
    session = store.get(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="recommendation session not found")

    if req.current_song_id:
        record_event(
            "playback",
            {
                "session_id": session_id,
                "song_id": req.current_song_id,
                "play_duration_seconds": req.play_duration_seconds,
                "skipped": True,
                "repeat_count": req.repeat_count,
            },
        )

    track = store.next_track(session_id)
    if track is None:
        raise HTTPException(status_code=404, detail="no more recommendations")

    return recommendation_response(
        session_id=session.session_id,
        track=track,
        state=session.state,
    )


@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    if get_session_store().get(req.session_id) is None:
        raise HTTPException(status_code=404, detail="recommendation session not found")

    record_event(
        "feedback",
        {
            "session_id": req.session_id,
            "song_id": req.song_id,
            "music_preference": req.music_preference,
            "regulation_effect": req.regulation_effect,
            "play_duration_seconds": req.play_duration_seconds,
            "skipped": req.skipped,
            "repeat_count": req.repeat_count,
        },
    )

    return {"status": "ok"}
