from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4


@dataclass
class RecommendationSession:
    session_id: str
    candidates: List[dict]
    state: dict
    cursor: int
    created_at: str


class SessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, RecommendationSession] = {}

    def create(self, candidates: List[dict], state: dict) -> RecommendationSession:
        if not candidates:
            raise ValueError("recommendation candidates cannot be empty")

        session = RecommendationSession(
            session_id=uuid4().hex,
            candidates=candidates,
            state=state,
            cursor=0,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[RecommendationSession]:
        return self._sessions.get(session_id)

    def next_track(self, session_id: str) -> Optional[dict]:
        session = self.get(session_id)
        if session is None or session.cursor + 1 >= len(session.candidates):
            return None

        session.cursor += 1
        return session.candidates[session.cursor]

    def has_next(self, session_id: str) -> bool:
        session = self.get(session_id)
        return bool(session and session.cursor + 1 < len(session.candidates))
