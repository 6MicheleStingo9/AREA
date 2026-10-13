"""Unit tests for the questionnaire logic (quiz/logic.py)."""

from quiz.logic import parse_followup_answers, should_show_followup, validate_answer

OPTIONS = ["A", "B", "C", "D", "E"]


class FakeForm(dict):
    """Minimal stand-in for Starlette's FormData (get + getlist)."""

    def getlist(self, key):
        value = self.get(key, [])
        return value if isinstance(value, list) else [value]


def checkbox_question(condition):
    return {
        "id": "9.9",
        "type": "checkbox",
        "options": OPTIONS,
        "follow_ups": [{"text": "Follow-up", "condition": condition}],
    }


def followup(condition):
    return {"text": "Follow-up", "condition": condition, "_parent_options": OPTIONS}


def test_option_index_in_checkbox_uses_option_indices():
    fu = followup({"type": "option_index_in", "value": [2, 3]})
    # "C" is option 2: pertinent even as the only selection
    assert should_show_followup(fu, {"selected": ["C"]}, "checkbox")
    # options 0, 1 and 4: not pertinent, however many are selected
    assert not should_show_followup(fu, {"selected": ["A", "B", "E"]}, "checkbox")
    assert not should_show_followup(fu, {"selected": [], "other": "x"}, "checkbox")


def test_always_on_checkbox_requires_a_real_choice():
    fu = followup({"type": "always"})
    assert not should_show_followup(fu, {"selected": [], "other": None, "other_checked": False}, "checkbox")
    assert should_show_followup(fu, {"selected": ["A"], "other": None}, "checkbox")


def test_parse_followup_answers_keeps_only_pertinent_ones():
    # The no-JS fallback renders every follow-up: answers to the ones not
    # pertinent to the submitted answer must be dropped.
    question = checkbox_question({"type": "option_index_in", "value": [3]})
    form = FakeForm({"followup_9.9_0": "typed text"})
    assert parse_followup_answers(question, {"selected": ["A"]}, form) == {}
    assert parse_followup_answers(question, {"selected": ["D"]}, form) == {"0": "typed text"}


def test_validate_multiple_choice_requires_an_option():
    question = {"id": "1", "type": "multiple_choice", "required": True, "options": OPTIONS}
    assert validate_answer(question, "", "it") == (False, "Seleziona un'opzione")
    assert validate_answer(question, "A", "it") == (True, "")
