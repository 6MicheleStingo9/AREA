import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from operator import add
from pathlib import Path
from typing import Annotated, Any, Dict, List

from jinja2 import Template
from langchain.messages import AnyMessage
from langgraph.graph import StateGraph
from pydantic import ValidationError
from typing_extensions import TypedDict

from agents.domain_analyzer.prompts import (
    DOMAIN_ANALYSIS_JSON_SCHEMA,
    DOMAIN_ANALYSIS_SYSTEM_PROMPT,
    DOMAIN_ANALYSIS_USER_PROMPT,
)
from utils.models import DomainAnalysisAdapter, DomainItem
from utils.utils import create_logger, get_llm_instance

_logger = create_logger("domain_analyzer")

# Setup paths
CURRENT_DIR = Path(__file__).parent
DOMAIN_DIR = Path(__file__).parent.parent.parent / "files" / "analysis" / "domain"


# ================================
# State definition
# ================================
class DomainAnalysisState(TypedDict, total=False):
    """State dictionary for domain analysis process."""

    metadata: Dict[str, Any]
    questionnaire: Dict[str, Any]
    analysis: Dict[str, Any]
    messages: Annotated[List[AnyMessage], add]
    errors: Annotated[List[str], add]


# ================================
# NODE 1 – Load file
# ================================
def node_load(state: DomainAnalysisState, file_path: str) -> DomainAnalysisState:
    """
    Load questionnaire JSON file into state.

    Args:
        state (DomainAnalysisState): Current state of the analysis.
        file_path (str): Path to the questionnaire JSON file.

    Returns:
        DomainAnalysisState: Updated state with loaded questionnaire or errors.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            state["questionnaire"] = json.load(f)
        # Ensure a unique run identifier exists for this analysis flow.
        meta = state.get("questionnaire", {}).get("metadata", {}) or {}
        run_id = meta.get("run_id") or uuid.uuid4().hex
        # store run_id into state metadata for downstream agents
        state.setdefault("metadata", {})
        state["metadata"]["run_id"] = run_id
        _logger.info(
            "Questionnaire loaded",
            step="load_file",
            keys=list(state["questionnaire"].keys()),
        )
        _logger.debug(
            "Questionnaire keys",
            step="load_file",
            keys=list(state["questionnaire"].keys()),
        )
    except FileNotFoundError as e:
        msg = (
            f"[DOMAIN][FATAL] load_questionnaire: file_not_found file_path={file_path}"
        )
        _logger.error(msg, exc_info=True)
        errs = state.setdefault("errors", [])
        if msg not in errs:
            errs.append(msg)
    except json.JSONDecodeError as e:
        msg = f"[DOMAIN][FATAL] load_questionnaire: invalid_json file_path={file_path} error={e.msg}"
        _logger.error(msg, exc_info=True)
        errs = state.setdefault("errors", [])
        if msg not in errs:
            errs.append(msg)

    return state


# ================================
# NODE 2 – Validate file
# ================================
def node_validate(state: DomainAnalysisState) -> DomainAnalysisState:
    """
    Validate the loaded questionnaire structure.

    Args:
        state (DomainAnalysisState): Current state of the analysis.

    Returns:
        DomainAnalysisState: Updated state with validation results.
    """
    data = state.get("questionnaire")
    if not data:
        msg = "Missing questionnaire"
        _logger.error(
            "Validation failed",
            step="validate",
            error=msg,
        )
        errs = state.setdefault("errors", [])
        if msg not in errs:
            errs.append(msg)
        return state

    for key in ["metadata", "responses"]:
        if key not in data:
            msg = f"Missing field: {key}"
            _logger.error(
                "Validation failed",
                step="validate",
                error=msg,
                missing_field=key,
            )
            errs = state.setdefault("errors", [])
            if msg not in errs:
                errs.append(msg)
            return state

    # Preserve existing run_id if present
    existing_run = (state.get("metadata") or {}).get("run_id")
    state["metadata"] = dict(data.get("metadata") or {})
    if existing_run and not state["metadata"].get("run_id"):
        state["metadata"]["run_id"] = existing_run

    _logger.info(
        "Validation succeeded",
        step="validate",
        metadata_keys=list(state["metadata"].keys()),
    )

    return state


# ================================
# _build_messages helper function
# ================================
def _build_messages(questions_and_answers: str, language: str) -> List[Any]:
    """
    Build messages for the LLM based on questions and answers and language.

    Args:
        questions_and_answers (str): Formatted string of questions and answers.
        language (str): Language code for localization.

    Returns:
        List[Any]: List of messages for LLM input.
    """
    system_msg = {
        "role": "system",
        "content": DOMAIN_ANALYSIS_SYSTEM_PROMPT,
    }
    # Render the user prompt with Jinja2, also passing the language
    user_prompt_template = Template(DOMAIN_ANALYSIS_USER_PROMPT)
    user_msg = {
        "role": "user",
        "content": user_prompt_template.render(
            questions_and_answers=questions_and_answers, language=language
        ),
    }
    return [system_msg, user_msg]


# ================================
# NODE 3 – Analyze with LLM
# ================================
def node_analyze(state: DomainAnalysisState) -> DomainAnalysisState:
    """
    Analyze the questionnaire responses using an LLM and structured output.

    Args:
        state (DomainAnalysisState): Current state of the analysis.

    Returns:
        DomainAnalysisState: Updated state with analysis results.
    """
    llm = get_llm_instance(t=0)
    data = state.get("questionnaire")
    if not data:
        msg = "analyze_responses: no_questionnaire"
        _logger.error(msg)
        state["errors"].append(msg)
        return state

    responses = data.get("responses", {})
    _logger.info(
        "Domain analysis start",
        step="analyze",
        responses_count=len(responses),
    )

    # Determine language for prompts. Default to 'en' if not specified.
    language = (data.get("metadata") or {}).get("language", "en")

    questions_and_answers = "\n".join(
        f"- Domain and sub-domain: {qid}\n"
        f"  Question: {resp.get('question')}\n"
        f"  Answer: {resp.get('answer')}"
        for qid, resp in responses.items()
    )

    state["messages"] = _build_messages(questions_and_answers, language)

    _logger.debug(
        "Messages prepared",
        step="analyze",
        roles=[m.get("role") for m in state["messages"]],
        language=language,
    )

    try:
        structured_llm = llm.with_structured_output(
            schema=DOMAIN_ANALYSIS_JSON_SCHEMA, method="json_schema"
        )
        _logger.info(
            "Invoking structured LLM",
            step="analyze",
            method="json_schema",
            language=language,
        )
        structured_resp = structured_llm.invoke(state["messages"])
        _logger.info("Structured response received", step="analyze")
        # Normalize to dict for TypeAdapter validation
        if hasattr(structured_resp, "parsed"):
            parsed = structured_resp.parsed
        elif isinstance(structured_resp, dict):
            parsed = structured_resp
        else:
            raise RuntimeError(
                f"Unexpected structured response type: {type(structured_resp)!r}"
            )

        # Validate the parsed output using Pydantic and convert to Python dict
        try:
            validated: Dict[str, DomainItem] = DomainAnalysisAdapter.validate_python(
                parsed
            )
            #  Convert Pydantic models to pure dicts for JSON serialization
            state["analysis"] = {k: v.model_dump() for k, v in validated.items()}
            _logger.info(
                "Domain analysis completed",
                step="analyze",
                domains=len(state["analysis"]),
                risks_total=sum(
                    len(v.get("risks", [])) for v in state["analysis"].values()
                ),
                language=language,
            )
            _logger.info("Domain analysis end", step="analyze")
            return state
        except ValidationError as ve:
            _logger.error(
                "Validation error on structured output",
                step="analyze",
                exc_info=True,
                errors=ve.errors(),
            )
            errs = state.setdefault("errors", [])
            err_msg = f"[DOMAIN][FATAL] validation_error: {ve.errors()}"
            if err_msg not in errs:
                errs.append(err_msg)
            return state

    except Exception as e:
        _logger.error(
            "Structured invocation failed",
            step="analyze",
            exc_info=True,
        )
        errs = state.setdefault("errors", [])
        err_msg = f"[DOMAIN][FATAL] {str(e)}"
        if err_msg not in errs:
            errs.append(err_msg)
        return state


# ================================
# _save_output helper function
# ================================
def _save_output(state: DomainAnalysisState) -> str:
    """
    Save the complete output in JSON.

    Args:
        state (DomainAnalysisState): Current state of the analysis.

    Returns:
        str: Path to the saved JSON file.
    """
    DOMAIN_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = state.get("metadata", {}).get("run_id")
    if not run_id:
        raise RuntimeError(
            "Missing run_id in state; ensure the flow starts from domain analyzer which creates run_id"
        )
    filename = f"domain_analysis_{run_id}.json"
    path = DOMAIN_DIR / filename
    meta = dict(state.get("metadata") or {})
    meta.update(
        {
            "timestamp": ts,
            "analysis_current_step": "domain_evaluation",
            "analysis_next_step": "causality_evaluation",
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
# NODE 4 – Save analysis
# ================================
def node_save(state: DomainAnalysisState) -> DomainAnalysisState:
    """
    Save the complete output in JSON.

    Args:
        state (DomainAnalysisState): Current state of the analysis.

    Returns:
        DomainAnalysisState: Updated state after saving.
    """
    try:
        out_path = _save_output(state)
        _logger.info(
            "Domain analysis saved",
            step="save",
            output_path=out_path,
            domains=len(state.get("analysis", {})),
            risks_total=sum(
                len(v.get("risks", [])) for v in state.get("analysis", {}).values()
            ),
        )
    except Exception as e:
        _logger.error("Failed saving domain analysis", exc_info=e)
        errs = state.setdefault("errors", [])
        err_msg = f"{str(e)}"
        if err_msg not in errs:
            errs.append(err_msg)
    return state


# ================================
# Graph construction
# ================================
def create_domain_analyzer_graph(file_path: str):
    """
    Create and compile the LangGraph graph for domain analysis.

    Args:
        file_path (str): Path to the questionnaire JSON file.

    Returns:
        StateGraph: Compiled LangGraph for domain analysis.
    """
    graph = StateGraph(DomainAnalysisState)

    # Register nodes (the signature always accepts state, extras are added here)
    graph.add_node("load_file", lambda state: node_load(state, file_path))
    graph.add_node("validate", node_validate)
    graph.add_node("analyze", node_analyze)
    graph.add_node("save", node_save)

    # Execution order
    graph.set_entry_point("load_file")
    graph.add_edge("load_file", "validate")
    graph.add_edge("validate", "analyze")
    graph.add_edge("analyze", "save")

    return graph.compile()


# ================================
# Standalone execution
# ================================
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Run analysis on a questionnaire JSON file (by run_id or filename)"
    )
    parser.add_argument(
        "--run_id",
        type=str,
        required=False,
        help="run_id of the questionnaire to analyze (optional if using filename)",
    )
    parser.add_argument(
        "filename",
        nargs="?",
        help="Name of the questionnaire JSON file (optional if using run_id)",
    )
    args = parser.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    answers_dir = os.path.join(repo_root, "files", "answers")

    # Search for file by run_id if provided
    input_file = None
    if args.run_id:
        candidate = os.path.join(answers_dir, f"answers_{args.run_id}.json")
        if os.path.isfile(candidate):
            input_file = candidate
        else:
            _logger.error(f"Answers file for run_id not found: {candidate}")
            sys.exit(2)
    elif args.filename:
        # If filename is an absolute path, use it directly
        if os.path.isabs(args.filename):
            input_file = args.filename
        else:
            candidate = os.path.join(answers_dir, args.filename)
            if os.path.isfile(candidate):
                input_file = candidate
            else:
                _logger.error(f"Answers file not found: {candidate}")
                sys.exit(2)
    else:
        _logger.error("You must specify --run_id or questionnaire filename.")
        sys.exit(2)

    graph = create_domain_analyzer_graph(input_file)

    initial_state: DomainAnalysisState = {
        "metadata": {},
        "questionnaire": {},
        "analysis": {},
        "messages": [],
        "errors": [],
    }

    final_state = graph.invoke(initial_state)

    if final_state.get("errors"):
        _logger.error(f"Execution completed with errors: {final_state['errors']}")
        sys.exit(1)
    else:
        _logger.info("Execution completed successfully.")
        sys.exit(0)
