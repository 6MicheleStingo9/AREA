"""Pure-Python quiz logic — Streamlit-free. Shared by the FastAPI layer and tests."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

FILES_DIR = Path(__file__).resolve().parent.parent / "files"


def load_questions(lang: str) -> List[Dict]:
    path = FILES_DIR / f"questions_{lang}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["questions"]


def should_show_followup(followup: Dict, answer: Any, question_type: str) -> bool:
    condition = followup.get("condition", {})
    ctype = condition.get("type")

    if ctype == "always":
        if question_type == "free_text":
            return bool(answer) and len(str(answer).strip()) >= 10
        if question_type == "checkbox":
            # A checkbox answer is always a (truthy) dict; require a real choice.
            if isinstance(answer, dict):
                return bool(answer.get("selected")) or bool(answer.get("other"))
            return False
        return bool(answer)

    elif ctype == "option_index":
        value = condition.get("value")
        if question_type == "multiple_choice":
            options = followup.get("_parent_options", [])
            if options and isinstance(answer, str) and answer in options:
                return options.index(answer) == value

    elif ctype == "option_index_in":
        values = condition.get("value", [])
        if question_type == "checkbox" and isinstance(answer, dict):
            # Compare the option indices of the selected options (not their
            # positions in the selection list).
            options = followup.get("_parent_options", [])
            selected = answer.get("selected", [])
            return any(options.index(s) in values for s in selected if s in options)
        elif question_type == "multiple_choice":
            options = followup.get("_parent_options", [])
            if options:
                if isinstance(answer, str):
                    idx = options.index(answer) if answer in options else -1
                    return idx in values
                elif isinstance(answer, list):
                    idxs = [options.index(a) for a in answer if a in options]
                    return any(idx in values for idx in idxs)

    return False


def validate_answer(question: Dict, answer: Any, lang: str = "en") -> Tuple[bool, str]:
    from quiz.translations import t as _t

    def t(key: str, **kwargs) -> str:
        return _t(key, lang=lang, **kwargs)

    if not question.get("required", False):
        return True, ""

    if question["type"] == "free_text":
        if not answer or not str(answer).strip():
            return False, t("this_question_is_required")
        min_length = question.get("validation", {}).get("min_length", 0)
        if len(answer) < min_length:
            return False, t("min_length_validation", min_length=min_length)

    elif question["type"] == "checkbox":
        is_dict = isinstance(answer, dict)
        selected = answer.get("selected", []) if is_dict else []
        other_text = answer.get("other") if is_dict else None
        # If "Other" is ticked, specifying its value is mandatory (regardless of
        # how many standard options are also selected).
        if is_dict and answer.get("other_checked") and not other_text:
            return False, t("specify_other_required")
        min_sel = question.get("min_selections", 1)
        total = len(selected) + (1 if other_text else 0)
        if total < min_sel:
            return False, t("min_selections_validation", min_selections=min_sel)

    elif question["type"] == "multiple_choice":
        if not answer or not str(answer).strip():
            return False, t("select_option")

    return True, ""


def parse_form_answer(question: Dict, form) -> Any:
    q_type = question["type"]
    q_id = question["id"]

    if q_type in ("free_text", "multiple_choice"):
        return form.get(f"q_{q_id}", "")
    elif q_type == "checkbox":
        selected = form.getlist(f"q_{q_id}")
        # The "Other" text counts only when its checkbox is actually ticked, so
        # a stale value left in a hidden field is ignored once "Other" is off.
        other_checked = bool(form.get(f"q_{q_id}_other_check"))
        other_text = (form.get(f"q_{q_id}_other") or "").strip() or None
        other = other_text if other_checked else None
        return {"selected": selected, "other": other, "other_checked": other_checked}
    return None


def parse_followup_answers(question: Dict, answer: Any, form) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for idx, followup in enumerate(question.get("follow_ups", [])):
        if question["type"] in ("multiple_choice", "checkbox"):
            followup["_parent_options"] = question.get("options", [])
        if should_show_followup(followup, answer, question["type"]):
            key = f"followup_{question['id']}_{idx}"
            result[str(idx)] = form.get(key, "")
    return result


def save_answers(
    answers: Dict, lang: str, questions_count: int, run_id: str | None = None
) -> Path:
    """Persist answers to disk.

    When ``run_id`` is provided it is embedded in both the filename and the
    metadata so the whole pipeline (domain → … → report) shares a single id and
    the generated report is addressable as ``ai_risk_report_<run_id>.html``.
    """
    out_dir = FILES_DIR / "answers"
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
    payload = {
        "metadata": metadata,
        "responses": answers,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return out_path
