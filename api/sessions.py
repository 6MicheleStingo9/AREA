"""In-memory quiz session store. State is lost on process restart."""

from typing import Any, Dict, List, Optional

_sessions: Dict[str, Dict[str, Any]] = {}


def create_session(session_id: str, lang: str, questions: List[Dict]) -> None:
    _sessions[session_id] = {
        "lang": lang,
        "questions": questions,
        "answers": {},
    }


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    return _sessions.get(session_id)


def update_session(session_id: str, **kwargs: Any) -> None:
    if session_id in _sessions:
        _sessions[session_id].update(kwargs)
