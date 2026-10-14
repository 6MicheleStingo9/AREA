"""
Causal classification with Laya, the local model of the causality step.

A Laya checkpoint fine-tuned on the MIT Causal Taxonomy (training/, README "Training (Laya)")
answers the three axes for each risk as typed `choice` questions and returns calibrated
probabilities. It reads the risk's subdomain in the MIT Domain Taxonomy (code and name), its
title and its explanation (`state`): the same text it was trained and evaluated on, built by the
same function (training/build_laya_data.py imports it from here).

torch, transformers and laya are imported only when the model is loaded, so this module, and
the LLM backend of the causality step, work without them.

Configuration (environment):
    LAYA_MODEL             checkpoint directory or Hugging Face id (default: the local
                           training/checkpoints/laya-causal-v4 when present, else the published
                           MicheleStingo/laya-kindynos-causal, downloaded on first use)
    LAYA_REVISION          Hub revision, for a Hugging Face id (default for the published model: v1.0)
    LAYA_REVIEW_THRESHOLD  confidence below which a label is flagged for review (default 0.9)
"""

import importlib.util
import json
import os
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from utils.paths import DATA, ROOT

MIT_DATABASE = DATA / "processed" / "full.jsonl"
DEFAULT_MODEL = ROOT / "training" / "checkpoints" / "laya-causal-v4"
# The published model, downloaded from Hugging Face on first use when there is no local checkpoint
HUB_MODEL, HUB_REVISION = "MicheleStingo/laya-kindynos-causal", "v1.0"
AXES = ("entity", "intent", "timing")
# Labels whose confidence (the calibrated probability of the chosen label) is below this are
# flagged for review. Chosen for laya-causal-v4 on the Kindynos validation runs
# (training/data/area_val.jsonl), not on the test set: label smoothing 0.1 caps the confidence
# near 0.93, where 274 of the 291 validation labels sit (93.8% correct); the 17 below 0.9 are 59%
# correct. Laya's own abstention threshold, fitted on the same runs for a 10% error (0.44),
# flags no label there.
REVIEW_THRESHOLD = 0.9

QUESTIONS: Dict[str, Dict[str, Any]] = {
    "entity": {
        "type": "choice",
        "instructions": "Who or what causes the risk, as the text frames it?",
        "criteria": {
            "ai": "The risk is caused by a decision or action made by an AI system",
            "human": "The risk is caused by a decision or action made by humans",
            "other": "The risk is caused by some other reason or is ambiguous",
        },
    },
    "intent": {
        "type": "choice",
        "instructions": "Does the risk come from an expected or an unexpected outcome of pursuing a goal?",
        "criteria": {
            "intentional": "The risk occurs due to an expected outcome from pursuing a goal",
            "unintentional": "The risk occurs due to an unexpected outcome from pursuing a goal",
            "other": "The risk is presented as occurring without clearly specifying the intentionality",
        },
    },
    "timing": {
        "type": "choice",
        "instructions": "When does the risk occur?",
        "criteria": {
            "pre-deployment": "The risk occurs before the AI is deployed",
            "post-deployment": "The risk occurs after the AI model has been trained and deployed",
            "other": "The risk is presented without a clearly specified time of occurrence",
        },
    },
}


class LayaUnavailable(RuntimeError):
    """The Laya model cannot be loaded: missing packages, checkpoint or download."""


def state(title: str, text: str, subdomain: Optional[Tuple[str, str]] = None) -> str:
    """What Laya reads: the subdomain (code, name) when known, the title, the description."""
    lines = [f"Risk subdomain: {subdomain[0]} {subdomain[1]}"] if subdomain else []
    return "\n".join(lines + ([title] if title else []) + [text])


@lru_cache(maxsize=1)
def subdomain_names() -> Dict[str, str]:
    """Subdomain code -> name, as in the MIT database."""
    with open(MIT_DATABASE, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return {r["subdomain_id"]: r["subdomain_name"] for r in rows if r["subdomain_id"]}


def model_spec() -> Tuple[str, Optional[str]]:
    """(checkpoint directory or Hugging Face id, revision): LAYA_MODEL and LAYA_REVISION when set, else
    the local checkpoint when present, else the published model at its release revision."""
    name, revision = os.getenv("LAYA_MODEL"), os.getenv("LAYA_REVISION") or None
    if name:
        return name, revision
    if DEFAULT_MODEL.is_dir():
        return str(DEFAULT_MODEL), None
    return HUB_MODEL, revision or HUB_REVISION


def model_name() -> str:
    """Short name of the configured model, for the report: the checkpoint folder or the Hub id."""
    name, _ = model_spec()
    return Path(name).name if _local_dir(name) or _is_path(name) else name


def review_threshold() -> float:
    return float(os.getenv("LAYA_REVIEW_THRESHOLD") or REVIEW_THRESHOLD)


def _is_path(name: str) -> bool:
    """True when `name` can only be a directory (the default, or an explicit path), not a Hub id."""
    return name == str(DEFAULT_MODEL) or name.startswith((".", "/", "~"))


def _local_dir(name: str) -> Optional[Path]:
    """The checkpoint directory `name` points to (absolute, or relative to the project), if any."""
    for path in (Path(name).expanduser(), ROOT / name):
        if path.is_dir():
            return path.resolve()
    return None


_NO_PACKAGES = (
    "The Laya packages are not installed: install torch, then requirements-laya.txt (README, "
    "'Causal classification'), or set CAUSALITY_BACKEND=llm to classify with the LLM."
)


def problem() -> Optional[str]:
    """Why the configured model cannot load, when that shows without loading it (missing
    checkpoint directory or packages); None otherwise."""
    name, _ = model_spec()
    if _local_dir(name) is None and _is_path(name):
        return (
            f"No Laya checkpoint at {name}. Set LAYA_MODEL to the checkpoint directory or Hugging Face id "
            "(README, 'Causal classification'), or CAUSALITY_BACKEND=llm to classify with the LLM."
        )
    if importlib.util.find_spec("laya") is None:
        return _NO_PACKAGES
    return None


_load_lock = threading.Lock()
_predict_lock = threading.Lock()
_agent = None


def _load() -> Any:
    issue = problem()
    if issue:
        raise LayaUnavailable(issue)
    name, revision = model_spec()
    local = _local_dir(name)
    if local is not None:
        # A local checkpoint carries its encoder config and tokenizer: no network needed.
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
    try:
        import laya
    except ImportError as e:
        raise LayaUnavailable(_NO_PACKAGES) from e
    target = str(local) if local else name
    try:
        return laya.load(target, revision=revision) if revision else laya.load(target)
    except Exception as e:
        raise LayaUnavailable(f"Cannot load the Laya model {target}: {e}") from e


def load() -> Any:
    """The Laya agent, loaded once per process (a few seconds on CPU)."""
    global _agent
    with _load_lock:
        if _agent is None:
            _agent = _load()
    return _agent


def classify(risks: Sequence[Tuple[Optional[str], str, str]]) -> List[Dict[str, Dict[str, Any]]]:
    """For each (subdomain code, title, explanation): {axis: {"value", "probabilities", "confidence"}}.

    One call per risk: on CPU, `predict_batch` was slower per risk than single calls. A subdomain
    code missing from the MIT database leaves the subdomain line out of the state.
    """
    agent = load()
    names = subdomain_names()
    out = []
    with _predict_lock:  # one prediction at a time: concurrent pipeline runs share the model
        for code, title, text in risks:
            res = agent.predict(state(title, text, (code, names[code]) if code in names else None), QUESTIONS)
            answers = {}
            for ax in AXES:
                probs = res["answers"][ax]["probabilities"]
                answers[ax] = {"value": res["answers"][ax]["choice"], "probabilities": probs, "confidence": max(probs.values())}
            out.append(answers)
    return out
