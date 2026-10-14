"""The progress of a pipeline run, for whoever follows it: the web interface shows the step in course.

The pipeline reports by run id: the step it starts, and the counts it knows ("risks", "labelled"). The
API listens to the runs it starts; a run started from the terminal has no listener, and its reports
go nowhere.
"""

import threading
from typing import Any, Callable, Dict, Optional

# The steps of a run, in order: the domain analysis, the causes, the expert rules, the report
STEPS = ("domain", "causes", "rules", "report")

Listener = Callable[..., None]

_listeners: Dict[str, Listener] = {}
_lock = threading.Lock()


def listen(run_id: str, listener: Listener) -> None:
    """Call listener(step, **counts) for each report of the run."""
    with _lock:
        _listeners[run_id] = listener


def forget(run_id: str) -> None:
    with _lock:
        _listeners.pop(run_id, None)


def report(run_id: Optional[str], step: str, **counts: Any) -> None:
    with _lock:
        listener = _listeners.get(run_id) if run_id else None
    if listener:
        listener(step, **counts)
