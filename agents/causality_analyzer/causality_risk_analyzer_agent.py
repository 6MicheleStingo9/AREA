import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph import StateGraph

from agents.causality_analyzer import laya_classifier
from agents.causality_analyzer.prompts import (
    CAUSALITY_JSON_SCHEMA,
    CAUSALITY_SYSTEM_PROMPT,
    CAUSALITY_USER_PROMPT,
)
from utils import progress
from utils.paths import ANALYSIS
from utils.utils import apply_retry, create_logger, get_llm_instance

_logger = create_logger("causality_analyzer")

CAUSALITY_DIR = ANALYSIS / "causality"

# Who labels the causality (CAUSALITY_BACKEND): "laya", the local fine-tuned classifier
# (laya_classifier.py, the default), or "llm", the configured LLM with the prompts in prompts.py.
BACKENDS = ("laya", "llm")

# Laya writes no text: each label gets the MIT definition of its value and the confidence; a
# label below the review threshold says so and names the next most likely value.
_LAYA_TEXT = {
    "en": {
        "definitions": {ax: q["criteria"] for ax, q in laya_classifier.QUESTIONS.items()},
        "labels": {
            "entity": {"ai": "AI", "human": "Human", "other": "Other"},
            "intent": {"intentional": "Intentional", "unintentional": "Unintentional", "other": "Other"},
            "timing": {"pre-deployment": "Pre-deployment", "post-deployment": "Post-deployment", "other": "Other"},
        },
        "assigned": "Label assigned by the local Laya model with {pct}% confidence.",
        "review": "Below the {threshold}% review threshold: check this label. Next most likely: {label} ({pct}%).",
    },
    "it": {
        "definitions": {
            "entity": {
                "ai": "Il rischio è causato da una decisione o da un'azione di un sistema di IA",
                "human": "Il rischio è causato da una decisione o da un'azione di esseri umani",
                "other": "Il rischio ha un'altra causa, oppure la causa è ambigua",
            },
            "intent": {
                "intentional": "Il rischio è un esito atteso del perseguimento di un obiettivo",
                "unintentional": "Il rischio è un esito inatteso del perseguimento di un obiettivo",
                "other": "Il rischio è presentato senza specificare chiaramente l'intenzionalità",
            },
            "timing": {
                "pre-deployment": "Il rischio si manifesta prima del rilascio del sistema di IA",
                "post-deployment": "Il rischio si manifesta dopo l'addestramento e il rilascio del modello",
                "other": "Il rischio è presentato senza indicare chiaramente quando si manifesta",
            },
        },
        "labels": {
            "entity": {"ai": "AI", "human": "Umano", "other": "Altro"},
            "intent": {"intentional": "Intenzionale", "unintentional": "Non intenzionale", "other": "Altro"},
            "timing": {"pre-deployment": "Pre-deployment", "post-deployment": "Post-deployment", "other": "Altro"},
        },
        "assigned": "Etichetta assegnata dal modello locale Laya con confidenza {pct}%.",
        "review": "Sotto la soglia di revisione del {threshold}%: da verificare. Seconda ipotesi: {label} ({pct}%).",
    },
}


def causality_backend() -> str:
    """The configured backend (CAUSALITY_BACKEND, default "laya")."""
    backend = (os.getenv("CAUSALITY_BACKEND") or "laya").strip().lower()
    if backend not in BACKENDS:
        raise ValueError(f"CAUSALITY_BACKEND must be one of {', '.join(BACKENDS)}, got {backend!r}")
    return backend


# ================================
# State definition
# ================================
class CausalAnalysisState(TypedDict, total=False):
    """State dictionary for causality analysis process."""

    metadata: Dict[str, Any]
    questionnaire: Dict[str, Any]
    analysis: Dict[str, Any]
    # Plain lists, no `add` reducer: nodes update and return the whole state, so a
    # reducer would append each list to itself and duplicate every entry.
    messages: List[AnyMessage]
    errors: List[str]


# ================================
# NODE 1 - Load Input
# ================================
def node_load(state: CausalAnalysisState) -> CausalAnalysisState:
    """
    Load initial state from domain analyzer output.

    Args:
        state: Initial state dictionary possibly containing 'analysis' key.

    Returns:
        Updated state dictionary with reset messages and errors.
    """
    # Reset messages and errors for a clean start
    state["messages"] = []
    state["errors"] = []

    # Ensure analysis is present (passed from domain_analyzer)
    if state.get("analysis") is None:
        err = "No analysis data present in initial state"
        _logger.error(err)
        errs = state.setdefault("errors", [])
        if err not in errs:
            errs.append(err)
        return state

    _logger.info(
        "Initial state received",
        step="load",
        source="domain_analyzer",
        has_analysis=bool(state.get("analysis")),
    )
    return state


# ================================
# NODE 2 - Validate Input
# ================================
def node_validate(state: CausalAnalysisState) -> CausalAnalysisState:
    """
    Validate the input analysis data.

    Args:
        state: State dictionary containing 'analysis' key.

    Returns:
        Updated state dictionary with validation errors if any.
    """
    analysis = state.get("analysis")
    if analysis is None:
        err = "No analysis data present to validate"
        _logger.error(err)
        errs = state.setdefault("errors", [])
        if err not in errs:
            errs.append(err)
        return state
    try:
        # Validate minimal expected shape: dict of domains with risks list (may be empty)
        for k, v in analysis.items():
            if not isinstance(v, dict) or "risks" not in v:
                raise ValueError(f"Domain {k} missing 'risks' list")
            if not isinstance(v["risks"], list):
                raise ValueError(f"Domain {k} 'risks' must be a list")
        _logger.info("Input validated", step="validate")
    except Exception as e:
        _logger.error("Validation error", exc_info=e)
        state.setdefault("errors", []).append(str(e))
    return state


# ================================
#  Utility function for building messages
# ================================
def _build_messages(analysis_json: Dict[str, Any], language: str) -> List[Any]:
    """
    Build messages for the LLM based on analysis JSON and language.

    Args:
        analysis_json: The domain analysis JSON data.
        language: The language for the analysis.

    Returns:
        A list of messages formatted for the LLM.
    """
    system_msg = {
        "role": "system",
        "content": CAUSALITY_SYSTEM_PROMPT.replace("{{language}}", language),
    }
    user_msg = {
        "role": "user",
        "content": CAUSALITY_USER_PROMPT.replace(
            "{{domain_analysis_json}}", json.dumps(analysis_json, ensure_ascii=False)
        ).replace("{{language}}", language),
    }
    return [system_msg, user_msg]


# ================================
#  Utility function for converting flat → nested
# ================================
def _flat_to_nested_risk(flat: dict) -> dict:
    """
    Convert a flat risk dictionary to a nested structure.

    Args:
        flat: The flat risk dictionary.

    Returns:
        A nested risk dictionary.
    """
    return {
        "title": flat["title"],
        "explanation": flat["explanation"],
        "severity": flat["severity"],
        "severity_rationale": flat.get("severity_rationale", ""),
        "mitigation": flat["mitigation"],
        "causality": {
            "entity": {
                "value": flat["entity"],
                "rationale": flat["entity_rationale"],
            },
            "intent": {
                "value": flat["intent"],
                "rationale": flat["intent_rationale"],
            },
            "timing": {
                "value": flat["timing"],
                "rationale": flat["timing_rationale"],
            },
        },
    }


# ================================
#  Utility function for converting entire analysis to nested
# ================================
def _convert_analysis_to_nested(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert the entire analysis from flat to nested structure.

    Args:
        analysis: The flat analysis dictionary.

    Returns:
        A nested analysis dictionary.
    """
    return {
        k: {"risks": [_flat_to_nested_risk(risk) for risk in v["risks"]]}
        for k, v in analysis.items()
    }


# ================================
#  Utility functions for the Laya backend
# ================================
def _laya_field(axis: str, answer: Dict[str, Any], language: str, threshold: float) -> Dict[str, Any]:
    """
    Build the causality block of one axis from Laya's answer.

    Args:
        axis: entity, intent or timing.
        answer: {"value", "probabilities", "confidence"} from laya_classifier.classify.
        language: The language of the report (texts in English unless Italian).
        threshold: Labels with a lower confidence are flagged for review.

    Returns:
        The value, a rationale (definition of the value and confidence), the confidence, the
        probabilities of all values and the review flag.
    """
    text = _LAYA_TEXT.get(language.split("-")[0].lower(), _LAYA_TEXT["en"])
    value, confidence = answer["value"], answer["confidence"]
    # Rounded down, so a label just below the threshold never shows the threshold itself
    rationale = f"{text['definitions'][axis][value]}. " + text["assigned"].format(pct=int(confidence * 100))
    review = confidence < threshold
    if review:
        label, p = sorted(answer["probabilities"].items(), key=lambda kv: kv[1], reverse=True)[1]
        rationale += " " + text["review"].format(
            threshold=round(threshold * 100), label=text["labels"][axis][label], pct=int(p * 100)
        )
    return {
        "value": value,
        "rationale": rationale,
        "confidence": round(confidence, 4),
        "probabilities": answer["probabilities"],
        "review": review,
    }


def _analyze_with_laya(analysis: Dict[str, Any], language: str, run_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Label every risk with Laya.

    Args:
        analysis: The domain analysis ('x.y' -> {"risks": [...]}).
        language: The language of the report.
        run_id: The run, to report how many risks have their labels (utils/progress.py).

    Returns:
        The nested analysis: the same subdomains and risks, in the same order, each risk with
        its causality block.
    """
    unknown = sorted(code for code in analysis if code not in laya_classifier.subdomain_names())
    if unknown:
        _logger.warning("Subdomains missing from the MIT database: Laya reads their risks without one", step="analyze", subdomains=unknown)
    items = [(code, risk) for code, block in analysis.items() for risk in block["risks"]]
    answers = laya_classifier.classify(
        [(code, risk["title"], risk["explanation"]) for code, risk in items],
        on_progress=lambda done: progress.report(run_id, "causes", risks=len(items), labelled=done),
    )
    threshold = laya_classifier.review_threshold()
    nested: Dict[str, Any] = {code: {"risks": []} for code in analysis}
    for (code, risk), answer in zip(items, answers):
        causality = {ax: _laya_field(ax, answer[ax], language, threshold) for ax in laya_classifier.AXES}
        nested[code]["risks"].append({**risk, "causality": causality})
    return nested


# ================================
#  Utility function for the LLM backend
# ================================
def _analyze_with_llm(state: CausalAnalysisState, analysis_json: Dict[str, Any], language: str) -> Dict[str, Any]:
    """
    Label every risk with the LLM.

    Args:
        state: State dictionary; its 'messages' receive the prompt.
        analysis_json: The domain analysis.
        language: The language for the rationales.

    Returns:
        The nested analysis with the causality block of every risk.
    """
    llm = get_llm_instance(t=0)
    messages = _build_messages(analysis_json, language)
    state["messages"] = messages
    _logger.debug(
        "Messages prepared",
        step="analyze",
        roles=[m.get("role") for m in state["messages"]],
        language=language,
    )

    # Prefer the same strategy as domain analyzer: structured output + TypeAdapter validation
    structured = apply_retry(
        llm.with_structured_output(
            schema=CAUSALITY_JSON_SCHEMA, method="json_schema"
        )
    )
    result = structured.invoke(messages)
    if hasattr(result, "parsed") and isinstance(result.parsed, dict):
        parsed = result.parsed
    elif isinstance(result, dict):
        parsed = result
    else:
        raise RuntimeError("Unexpected structured response type")

    # Convert flat structure to nested structure
    return _convert_analysis_to_nested(parsed)


# ================================
# NODE 3 - Analyze (Laya or LLM)
# ================================
def node_analyze(state: CausalAnalysisState) -> CausalAnalysisState:
    """
    Perform causality analysis with the configured backend (CAUSALITY_BACKEND).

    Args:
        state: State dictionary containing 'analysis' key.

    Returns:
        Updated state dictionary with causality analysis results, and the backend that
        produced them in metadata['causality_model'].
    """
    if state.get("errors"):
        return state  # invalid input: nothing to label
    analysis_json = state.get("analysis")
    metadata = dict(state.get("metadata") or {})

    # Retrieve language from metadata, default to 'en'
    language = metadata.get("language", "en")

    try:
        backend = causality_backend()
        if backend == "laya":
            model = {"backend": "laya", "model": laya_classifier.model_name(), "review_threshold": laya_classifier.review_threshold()}
            _logger.info("Causality analysis start", step="analyze", language=language, **model)
            state["analysis"] = _analyze_with_laya(analysis_json, language, metadata.get("run_id"))
        else:
            model = {"backend": "llm", "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash")}
            _logger.info("Causality analysis start", step="analyze", language=language, **model)
            state["analysis"] = _analyze_with_llm(state, analysis_json, language)
        metadata["causality_model"] = model
        state["metadata"] = metadata
        _logger.info("Causality analysis completed", step="analyze", language=language, backend=backend)
    except Exception as e:
        _logger.error("Causality analysis failed", step="analyze", exc_info=e)
        state.setdefault("errors", []).append(str(e))

    return state


# ================================
# _save_output helper function
# ================================
def _save_output(state: CausalAnalysisState) -> Optional[str]:
    """
    Save the complete output in JSON.

    Args:
        state: State dictionary containing 'analysis' and 'metadata'.

    Returns:
        The path to the saved JSON file.
    """
    CAUSALITY_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    run_id = (state.get("metadata") or {}).get("run_id")
    if not run_id:
        raise RuntimeError(
            "Missing run_id in state; run must start from domain analyzer"
        )
    filename = f"causality_analysis_{run_id}.json"
    path = CAUSALITY_DIR / filename
    meta = dict(state.get("metadata") or {})
    meta.update(
        {
            "timestamp": ts,
            "analysis_current_step": "causality_evaluation",
            "analysis_next_step": "heuristic_evaluation",
            "errors": state.get("errors", []),
        }
    )

    payload = {
        "metadata": meta,
        "analysis": state.get("analysis"),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)
    return str(path)


# ================================
# NODE 4 - Save Output
# ================================
def node_save(state: CausalAnalysisState) -> CausalAnalysisState:
    """
    Save the complete output in JSON.

    Args:
        state: State dictionary containing 'analysis' and 'metadata'.

    Returns:
        Updated state dictionary.
    """
    try:
        out_path = _save_output(state)

        _logger.info(
            "Causality analysis saved",
            step="save",
            output_path=out_path,
            domains=len(state.get("analysis", {})),
            risks_total=sum(
                len(v.get("risks", [])) for v in state.get("analysis", {}).values()
            ),
        )
    except Exception as e:
        _logger.error("Failed saving causality analysis", step="save", exc_info=e)
        state.setdefault("errors", []).append(f"{str(e)}")
        err_msg = f"{str(e)}"
        errs = state.setdefault("errors", [])
        if err_msg not in errs:
            errs.append(err_msg)
    return state


# ================================
# Graph construction
# ================================
def create_causality_analyzer_graph():
    """
    Create and compile the LangGraph graph for causality analysis.

    Returns:
        Compiled StateGraph for causality analysis.
    """
    graph = StateGraph(CausalAnalysisState)

    graph.add_node("Load", node_load)
    graph.add_node("Validate", node_validate)
    graph.add_node("Analyze", node_analyze)
    graph.add_node("Save", node_save)

    graph.add_edge("Load", "Validate")
    graph.add_edge("Validate", "Analyze")
    graph.add_edge("Analyze", "Save")
    graph.set_entry_point("Load")
    return graph.compile()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run causality analysis on a domain analysis JSON file."
    )
    parser.add_argument(
        "filename",
        help="Name of the domain analysis JSON file.",
    )
    args = parser.parse_args()

    # Build input file path from fixed directory
    input_file = ANALYSIS / "domain" / args.filename

    # Verify that the file exists
    if not os.path.isfile(input_file):
        _logger.error(f"Input file not found: {input_file}")
        sys.exit(2)

    # Load the domain analysis file
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            domain_analysis = json.load(f)
    except Exception as e:
        _logger.error(f"Failed to load input file: {e}")
        sys.exit(2)

    # Create the graph for causality analysis
    graph = create_causality_analyzer_graph()

    # Initial state
    initial_state: CausalAnalysisState = {
        "metadata": domain_analysis.get("metadata", {}),
        "analysis": domain_analysis.get("analysis", {}),
        "messages": [],
        "errors": [],
    }

    # Execute the graph
    final_state = graph.invoke(initial_state)

    # Handle the result
    if final_state.get("errors"):
        _logger.error(f"Execution completed with errors: {final_state['errors']}")
        sys.exit(1)
    else:
        _logger.info("Execution completed successfully.")
        sys.exit(0)
