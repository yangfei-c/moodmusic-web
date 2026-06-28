from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict

from app.config import feedback_log_path


def record_event(event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    feedback_log_path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "event_type": event_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }

    with open(feedback_log_path, "a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event
