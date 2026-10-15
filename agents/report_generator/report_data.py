"""
The data of the HTML report, prepared from the outputs of the pipeline.

The report is an app (frontend/report), built once into a single HTML file: html_generator.py writes
these data into a copy of it for each run. Everything the report shows is here: the results of the
expert rules, the data of its charts, and the risks with their causes and the answers behind them.
The charts count as the reports before them did: the same numbers, drawn in a new way.

frontend/report/src/data.ts describes the same structure for the app, and
frontend/report/src/test/example.json is the example run as this module prepares it
(tests/test_report_data.py keeps the two in step).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

# The version of the structure: the app reads only the one it was built for
VERSION = 1
LANGUAGES = ("en", "it")
DOMAINS = ("1", "2", "3", "4", "5", "6", "7")
SEVERITIES = ("high", "medium", "low")
# The values of each causal axis, in the order of the MIT Causal Taxonomy: anything else reads as "other"
CAUSES = {
    "entity": ("ai", "human", "other"),
    "intent": ("intentional", "unintentional", "other"),
    "timing": ("pre-deployment", "post-deployment", "other"),
}

# The patterns of the expert rules (agents/heuristic_analyzer/rules.pl), in the group where the
# heuristic analysis counts them, with the cause their rule names ("any" when it names none)
PATTERNS = {
    "critical": {
        "critical_ai_risks": "ai",
        "malicious_human_risks": "human",
        "high_threat_attacks": "human",
        "unintended_ai_failures": "ai",
        "human_error_risks": "human",
        "intentional_ai_risks": "ai",
        "preventable_critical_ai_risks": "ai",
        "critical_human_errors": "human",
        "low_priority_preventable": "any",
    },
    "moderate": {
        "moderate_operational_risks": "any",
        "moderate_ai_risks": "ai",
        "moderate_human_risks": "human",
        "moderate_intentional_ai_risks": "ai",
        "moderate_human_intentional_risks": "human",
    },
    "prevention": {
        "preventable_ai_risks": "ai",
        "preventable_human_risks": "human",
        "preventable_intentional_threats": "any",
    },
    "low": {
        "low_operational_risks": "any",
    },
}

# What the report step wrote when Gemini could not write the summary, before the report said it itself
_NO_SUMMARY = "Executive summary not available due to generation error."


def language_of(metadata: Dict[str, Any]) -> str:
    """The language of the run, "en" unless it is one that the report speaks."""
    lang = str(metadata.get("language") or "en").split("-")[0].lower()
    return lang if lang in LANGUAGES else "en"


def _percent(part: float, total: float) -> float:
    return part * 100 / total if total > 0 else 0.0


def _subdomains(analysis: Dict[str, Any]) -> List[str]:
    """The subdomain ids of the analysis in the order of the taxonomy: 1.1, 1.2, ..., 7.6."""

    def order(code: str):
        return tuple(int(part) if part.isdigit() else part for part in code.split("."))

    return sorted(analysis, key=order)


def _risks_of(analysis: Dict[str, Any], code: str) -> List[Dict[str, Any]]:
    block = analysis.get(code) or {}
    return [risk for risk in block.get("risks") or [] if isinstance(risk, dict)]


def _value(axis: str, risk: Dict[str, Any]) -> str:
    field = (risk.get("causality") or {}).get(axis) or {}
    value = str(field.get("value") or "").lower()
    return value if value in CAUSES[axis] else "other"


def results(heuristic: Dict[str, Any]) -> Dict[str, Any]:
    """The verdict of the expert rules: score, level, primary concern, recommended action, and the
    domains with the most high-severity risks (none without such risks)."""
    summary = heuristic.get("executive_summary") or {}
    score = summary.get("global_risk_score")
    return {
        "score": float(score) if isinstance(score, (int, float)) else None,
        "level": summary.get("overall_risk_level"),
        "concern": summary.get("primary_concern"),
        "action": summary.get("recommended_action"),
        "critical_domains": [
            {"id": str(domain["domain"]), "high": int(domain.get("high_count") or 0)}
            for domain in summary.get("top_3_critical_domains") or []
            if isinstance(domain, dict) and domain.get("domain") is not None
        ],
    }


def alerts(heuristic: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The alerts that the rules raised, in their order, each with its value (a count or a percentage)."""
    found = (heuristic.get("patterns") or {}).get("alerts") or {}
    return [
        {"id": name, "value": alert.get("value")}
        for name, alert in found.items()
        if isinstance(alert, dict) and alert.get("alert")
    ]


def counts(heuristic: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """How many risks, in how many domains and subdomains, by severity and by each cause."""
    counting = heuristic.get("counting") or {}

    def by(key: str, values) -> Dict[str, int]:
        found = counting.get(key) or {}
        return {value: int(found.get(value) or 0) for value in values}

    return {
        "risks": int(counting.get("total_risks") or 0),
        "domains": sum(1 for count in (counting.get("by_domain") or {}).values() if count),
        "subdomains": sum(1 for code in analysis if _risks_of(analysis, code)),
        "severity": by("by_severity", SEVERITIES),
        "entity": by("by_entity", CAUSES["entity"]),
        "intent": by("by_intent", CAUSES["intent"]),
        "timing": by("by_timing", CAUSES["timing"]),
    }


def domains(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The risks of each of the seven domains, by severity."""
    rows = []
    for domain in DOMAINS:
        row = {"id": domain, "high": 0, "medium": 0, "low": 0}
        for code in analysis:
            if code.startswith(domain + "."):
                for risk in _risks_of(analysis, code):
                    severity = str(risk.get("severity") or "").lower()
                    if severity in SEVERITIES:
                        row[severity] += 1
        rows.append(row)
    return rows


def profile(heuristic: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The alert and safety profile: eight indices on five axes, the criticality ones and the safety
    ones, as percentages of the risks. Exposure has no safety index and entity no criticality one."""
    counting = heuristic.get("counting") or {}
    total = counting.get("total_risks") or 0
    severity = counting.get("by_severity") or {}
    timing = counting.get("by_timing") or {}
    intent = counting.get("by_intent") or {}
    entity = counting.get("by_entity") or {}

    def share(count) -> float:
        return round(_percent(count or 0, total), 1)

    preventable = _percent(timing.get("pre-deployment") or 0, total)
    return [
        {
            "axis": "severity",
            "criticality": share(severity.get("high")),  # risk concentration
            "safety": share((severity.get("low") or 0) + (severity.get("medium") or 0)),  # impact control
        },
        {"axis": "exposure", "criticality": share(timing.get("post-deployment")), "safety": None},  # operational exposure
        {
            "axis": "prevention",
            "criticality": round(100 - preventable, 1),  # prevention deficit
            "safety": round(preventable, 1),  # preventability
        },
        {
            "axis": "intent",
            "criticality": share(intent.get("intentional")),  # threat intensity
            "safety": share(intent.get("unintentional")),  # safety culture
        },
        {"axis": "entity", "criticality": None, "safety": share(entity.get("human"))},  # human-caused share
    ]


def flow(analysis: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """How the risks go from their entity to their intent, and from their intent to their timing."""
    pairs = {"entity_intent": {}, "intent_timing": {}}
    for code in analysis:
        for risk in _risks_of(analysis, code):
            entity, intent, timing = (_value(axis, risk) for axis in CAUSES)
            pairs["entity_intent"][(entity, intent)] = pairs["entity_intent"].get((entity, intent), 0) + 1
            pairs["intent_timing"][(intent, timing)] = pairs["intent_timing"].get((intent, timing), 0) + 1
    sources = {"entity_intent": ("entity", "intent"), "intent_timing": ("intent", "timing")}
    out = {}
    for name, found in pairs.items():
        left, right = sources[name]
        out[name] = [
            {"from": a, "to": b, "count": found[(a, b)]}
            for a in CAUSES[left]
            for b in CAUSES[right]
            if found.get((a, b))
        ]
    return out


def patterns(heuristic: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Every pattern of the rules with its group, its cause and the risks it matches. A pattern the
    rules count but this module does not know yet comes last in its group, with any cause."""
    found = heuristic.get("patterns") or {}
    out = []
    for category, known in PATTERNS.items():
        group = found.get(f"{category}_patterns") or {}
        for pattern, cause in known.items():
            out.append({"id": pattern, "category": category, "cause": cause, "count": int(group.get(pattern) or 0)})
        for pattern, count in group.items():
            if pattern not in known:
                out.append({"id": pattern, "category": category, "cause": "any", "count": int(count or 0)})
    return out


def _cause(axis: str, risk: Dict[str, Any]) -> Dict[str, Any]:
    """One causal label: its value, and what labelled it gave: a rationale (the LLM), or the confidence
    and the probability of every value (Laya)."""
    field = (risk.get("causality") or {}).get(axis) or {}
    confidence = field.get("confidence")
    probabilities = field.get("probabilities")
    rationale = field.get("rationale")
    return {
        "value": _value(axis, risk),
        "rationale": rationale.strip() or None if isinstance(rationale, str) else None,
        "confidence": float(confidence) if isinstance(confidence, (int, float)) else None,
        "probabilities": (
            {str(value): float(p) for value, p in probabilities.items() if isinstance(p, (int, float))}
            if isinstance(probabilities, dict)
            else None
        ),
    }


def _text(value: Any) -> Optional[str]:
    return value.strip() or None if isinstance(value, str) else None


def risks(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Every risk, subdomain by subdomain, with an id (subdomain and position) and its three causes."""
    out = []
    for code in _subdomains(analysis):
        for position, risk in enumerate(_risks_of(analysis, code), start=1):
            out.append(
                {
                    "id": f"{code}-{position}",
                    "subdomain": code,
                    "title": _text(risk.get("title")) or "",
                    "explanation": _text(risk.get("explanation")),
                    # One of SEVERITIES: the domain analysis checks it (utils/models.py)
                    "severity": str(risk.get("severity") or "").lower(),
                    "severity_rationale": _text(risk.get("severity_rationale")),
                    "mitigation": _text(risk.get("mitigation")),
                    "causes": {axis: _cause(axis, risk) for axis in CAUSES},
                }
            )
    return out


def _answer(value: Any) -> Any:
    """An answer as text, or as the options chosen with the text of "Other"; None when there is none."""
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        selected = [str(option) for option in value.get("selected") or [] if str(option).strip()]
        other = _text(value.get("other"))
        return {"selected": selected, "other": other} if selected or other else None
    if isinstance(value, list):
        selected = [str(option) for option in value if str(option).strip()]
        return {"selected": selected, "other": None} if selected else None
    return None


def _followups(texts: Any, definitions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """The follow-ups that have an answer, with their question: by index ({"0": "..."}), or in a list."""
    if isinstance(texts, dict):
        items = sorted((int(key), text) for key, text in texts.items() if str(key).isdigit())
    elif isinstance(texts, list):
        items = list(enumerate(texts))
    else:
        items = []
    out = []
    for index, text in items:
        answer = _text(text)
        if answer and 0 <= index < len(definitions) and definitions[index].get("text"):
            out.append({"question": definitions[index]["text"], "answer": answer})
    return out


def answers(questionnaire: Optional[Dict[str, Any]], questions: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """The answers behind the risks, by question id (the subdomain): the question, the answer and the
    follow-ups. The follow-ups are saved by index: the questions of the run give their text."""
    questionnaire = questionnaire or {}
    responses = questionnaire.get("responses", questionnaire)
    by_id = {question.get("id"): question for question in questions or [] if isinstance(question, dict)}
    out = {}
    for code, response in (responses or {}).items():
        if not isinstance(response, dict):
            continue
        question = by_id.get(code) or {}
        out[code] = {
            "question": _text(response.get("question")) or _text(question.get("question")),
            "answer": _answer(response.get("answer")),
            "followups": _followups(response.get("followups"), question.get("follow_ups") or []),
        }
    return out


def _summary(metadata: Dict[str, Any]) -> Optional[str]:
    text = _text(metadata.get("executive_summary_text"))
    return None if text == _NO_SUMMARY else text


def _causality_model(metadata: Dict[str, Any]) -> Optional[Dict[str, str]]:
    model = metadata.get("causality_model")
    if not isinstance(model, dict) or model.get("backend") not in ("laya", "llm"):
        return None
    return {"backend": model["backend"], "model": str(model.get("model") or "")}


def report_data(
    metadata: Dict[str, Any],
    heuristic: Dict[str, Any],
    analysis: Dict[str, Any],
    questionnaire: Optional[Dict[str, Any]] = None,
    questions: Optional[List[Dict[str, Any]]] = None,
    created: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Everything the report of a run shows.

    Args:
        metadata: The metadata of the run: id, language, name of the system, summary, causal model.
        heuristic: The output of the expert rules.
        analysis: The risks by subdomain, each with its causality.
        questionnaire: The answers file of the run ({"metadata", "responses"}), or its responses.
        questions: The questions of the run, which give the text of the follow-ups.
        created: When the report was made (ISO 8601); now, by default.

    Returns:
        The data that html_generator.py writes into the report.
    """
    heuristic, analysis = heuristic or {}, analysis or {}
    answered, total = metadata.get("answered_questions"), metadata.get("total_questions")
    return {
        "version": VERSION,
        "run_id": str(metadata.get("run_id") or ""),
        "language": language_of(metadata),
        "system_name": _text(metadata.get("system_name")),
        "created": created or datetime.now().isoformat(timespec="seconds"),
        "questions": {
            "answered": answered if isinstance(answered, int) else None,
            "total": total if isinstance(total, int) else None,
        },
        "summary": _summary(metadata),
        "causality_model": _causality_model(metadata),
        "results": results(heuristic),
        "alerts": alerts(heuristic),
        "counts": counts(heuristic, analysis),
        "domains": domains(analysis),
        "profile": profile(heuristic),
        "flow": flow(analysis),
        "patterns": patterns(heuristic),
        "risks": risks(analysis),
        "answers": answers(questionnaire, questions),
        # The output of the rules as they wrote it, for "View data"
        "heuristic": heuristic,
    }
