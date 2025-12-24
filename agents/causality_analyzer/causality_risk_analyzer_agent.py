import argparse
import json
import os
import sys
import time
from operator import add
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph import StateGraph

from agents.causality_analyzer.prompts import (
    CAUSALITY_JSON_SCHEMA,
    CAUSALITY_SYSTEM_PROMPT,
    CAUSALITY_USER_PROMPT,
)
from utils.utils import create_logger, get_llm_instance

_logger = create_logger("causality_analyzer")

# Setup paths
CURRENT_DIR = Path(__file__).parent
CAUSALITY_DIR = Path(__file__).parent.parent.parent / "files" / "analysis" / "causality"


# ================================
# State definition
# ================================
class CausalAnalysisState(TypedDict, total=False):
    """State dictionary for causality analysis process."""

    metadata: Dict[str, Any]
    questionnaire: Dict[str, Any]
    analysis: Dict[str, Any]
    messages: Annotated[List[AnyMessage], add]
    errors: Annotated[List[str], add]


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
        "content": CAUSALITY_SYSTEM_PROMPT,
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
# NODE 3 - Analyze with LLM
# ================================
def node_analyze(state: CausalAnalysisState) -> CausalAnalysisState:
    """
    Perform causality analysis using the LLM.

    Args:
        state: State dictionary containing 'analysis' key.

    Returns:
        Updated state dictionary with causality analysis results.
    """
    analysis_json = state.get("analysis")
    llm = get_llm_instance(t=0)

    # Retrieve language from metadata, default to 'en'
    language = (state.get("metadata") or {}).get("language", "en")

    messages = _build_messages(analysis_json, language)
    state["messages"] = messages
    _logger.info("Causality analysis start", step="analyze", language=language)
    _logger.debug(
        "Messages prepared",
        step="analyze",
        roles=[m.get("role") for m in state["messages"]],
        language=language,
    )

    # Prefer the same strategy as domain analyzer: structured output + TypeAdapter validation
    structured = llm.with_structured_output(
        schema=CAUSALITY_JSON_SCHEMA, method="json_schema"
    )
    try:
        result = structured.invoke(messages)
        if hasattr(result, "parsed") and isinstance(result.parsed, dict):
            parsed = result.parsed
        elif isinstance(result, dict):
            parsed = result
        else:
            raise RuntimeError("Unexpected structured response type")

        # Convert flat structure to nested structure
        state["analysis"] = _convert_analysis_to_nested(parsed)
        _logger.info("Causality analysis completed", step="analyze", language=language)
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
    domain_dir = "/home/stingom/Scrivania/Git/area/files/analysis/domain"
    input_file = os.path.join(domain_dir, args.filename)

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
