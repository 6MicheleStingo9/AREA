"""The questionnaire: its questions, the follow-ups that an answer opens, the checks on an answer, and
the file of answers that the pipeline reads.

The web interface sends one answer per question, by question id:

- free_text: {"text": "..."}
- multiple_choice: {"choice": 0}, the index of the option
- checkbox: {"choices": [0, 2], "other": "..."}, with "other" absent while "Other" is not ticked

each with its follow-ups by index: "followups": {"0": "..."}. The interface applies the same rules as
you answer (frontend/web/src/questionnaire/logic.ts): the cases in
tests/fixtures/questionnaire_cases.json keep the two in step.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.paths import ANSWERS, FILES

Answer = Dict[str, Any]
Error = Dict[str, Any]


def load_questions(lang: str) -> List[Dict]:
    path = FILES / f"questions_{lang}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["questions"]


def _choices(question: Dict, answer: Answer) -> List[int]:
    """The options chosen, as indices: one for a multiple choice, any number for a checkbox."""
    if question["type"] == "multiple_choice":
        choice = answer.get("choice")
        return [] if choice is None else [choice]
    if question["type"] == "checkbox":
        return sorted(set(answer.get("choices") or []))
    return []


def _other(answer: Answer) -> str:
    return (answer.get("other") or "").strip()


def _shows(followup: Dict, question: Dict, answer: Answer) -> bool:
    condition = followup.get("condition", {})
    kind = condition.get("type")
    chosen = _choices(question, answer)
    if kind == "always":
        if question["type"] == "free_text":
            # From the start: shown once the answer was written, it appeared on the click on Next,
            # and moved the button from under the cursor
            return True
        return bool(chosen) or bool(_other(answer))
    if kind == "option_index":
        return question["type"] == "multiple_choice" and condition.get("value") in chosen
    if kind == "option_index_in":
        return any(index in condition.get("value", []) for index in chosen)
    return False


def visible_followups(question: Dict, answer: Answer) -> List[int]:
    """The indices of the follow-ups that the answer opens."""
    return [i for i, followup in enumerate(question.get("follow_ups", [])) if _shows(followup, question, answer)]


def answer_errors(question: Dict, answer: Optional[Answer]) -> List[Error]:
    """What is missing or wrong in the answer to a question, as codes: [] when it is complete."""
    answer = answer or {}
    errors: List[Error] = []
    kind = question["type"]
    required = question.get("required", False)
    if kind == "free_text":
        text = (answer.get("text") or "").strip()
        limits = question.get("validation", {})
        if not text:
            if required:
                errors.append({"code": "required"})
        elif len(text) < limits.get("min_length", 0):
            errors.append({"code": "min_length", "min": limits["min_length"]})
        elif "max_length" in limits and len(text) > limits["max_length"]:
            errors.append({"code": "max_length", "max": limits["max_length"]})
    else:
        options = question.get("options", [])
        chosen = _choices(question, answer)
        if any(not 0 <= index < len(options) for index in chosen):
            errors.append({"code": "unknown_option"})
        elif kind == "multiple_choice":
            if required and not chosen:
                errors.append({"code": "required"})
        elif "other" in answer and answer["other"] is not None and not _other(answer):
            # "Other" ticked: it needs its text, however many options are chosen besides
            errors.append({"code": "other_required"})
        else:
            least = question.get("min_selections", 1) if required else 0
            if len(chosen) + (1 if _other(answer) else 0) < least:
                errors.append({"code": "min_selections", "min": least})
    followups = question.get("follow_ups", [])
    texts = answer.get("followups") or {}
    for index in visible_followups(question, answer):
        if followups[index].get("required") and not (texts.get(str(index)) or "").strip():
            errors.append({"code": "followup_required", "followup": index})
    return errors


def validate_assessment(questions: List[Dict], answers: Dict[str, Answer]) -> Dict[str, List[Error]]:
    """The errors of every question that has some, by question id."""
    errors = {q["id"]: answer_errors(q, answers.get(q["id"])) for q in questions}
    return {qid: found for qid, found in errors.items() if found}


def _in_words(question: Dict, answer: Answer) -> Any:
    """The answer as the pipeline and the report read it: the text of the options, not their index."""
    if question["type"] == "free_text":
        return (answer.get("text") or "").strip()
    options = question.get("options", [])
    chosen = [options[i] for i in _choices(question, answer)]
    if question["type"] == "multiple_choice":
        return chosen[0] if chosen else ""
    return {"selected": chosen, "other": _other(answer) or None}


def responses(questions: List[Dict], answers: Dict[str, Answer]) -> Dict[str, Dict]:
    """The answers for the file the pipeline reads: by question id, the question, the answer in words,
    and the follow-ups it opened that have a text."""
    out = {}
    for question in questions:
        answer = answers.get(question["id"])
        if not answer:
            continue
        texts = answer.get("followups") or {}
        followups = {
            str(i): texts[str(i)].strip()
            for i in visible_followups(question, answer)
            if (texts.get(str(i)) or "").strip()
        }
        out[question["id"]] = {
            "question": question["question"],
            "answer": _in_words(question, answer),
            "followups": followups,
        }
    return out


def save_answers(
    answers: Dict,
    lang: str,
    questions_count: int,
    run_id: str | None = None,
    system_name: str | None = None,
) -> Path:
    """Persist answers to disk.

    When ``run_id`` is provided it is embedded in both the filename and the
    metadata so the whole pipeline (domain → … → report) shares a single id and
    the generated report is addressable as ``ai_risk_report_<run_id>.html``.

    ``system_name``, the name of the AI system that the user may give, goes to the metadata for the
    report: no prompt reads the metadata, so the name never reaches the LLM.
    """
    out_dir = ANSWERS
    out_dir.mkdir(parents=True, exist_ok=True)
    name = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"answers_{name}.json"
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "language": lang,
        "total_questions": questions_count,
        "answered_questions": len(answers),
    }
    if run_id:
        metadata["run_id"] = run_id
    if system_name:
        metadata["system_name"] = system_name
    payload = {
        "metadata": metadata,
        "responses": answers,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return out_path
