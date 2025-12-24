import json
import os
import sys
import time
from operator import add
from pathlib import Path
from typing import Annotated, Any, Dict, List, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph import StateGraph

from agents.report_generator.html_generator import generate_html_report
from agents.report_generator.prompts import (
    EXECUTIVE_SUMMARY_SYSTEM_PROMPT,
    EXECUTIVE_SUMMARY_USER_PROMPT,
)
from utils.utils import create_logger, get_llm_instance


# ================================
# Executive Summary Generation
# ================================
def _build_messages(heuristic, analysis, language):
    """Build messages for executive summary generation.

    Args:
        heuristic (dict): The heuristic analysis data.
        analysis (dict): The overall analysis data.
        language (str): The language for the summary.

     Returns: List[Dict[str, str]]: The list of messages for the LLM.
    """
    system_msg = {
        "role": "system",
        "content": EXECUTIVE_SUMMARY_SYSTEM_PROMPT,
    }
    heuristic_str = json.dumps(heuristic, ensure_ascii=False, indent=2)
    analysis_str = json.dumps(analysis, ensure_ascii=False, indent=2)
    usr_msg = {
        "role": "user",
        "content": EXECUTIVE_SUMMARY_USER_PROMPT.replace("{{heuristic}}", heuristic_str)
        .replace("{{analysis}}", analysis_str)
        .replace("{{language}}", language),
    }

    return [system_msg, usr_msg]


def generate_executive_summary_text(heuristic, analysis, language) -> str:
    """Generate the executive summary text using the LLM.

    Args:
        heuristic (dict): The heuristic analysis data.
        analysis (dict): The overall analysis data.
        language (str): The language for the summary.

    Returns:
        str: The generated executive summary text.
    """
    llm = get_llm_instance(t=0.2)
    messages = _build_messages(heuristic, analysis, language)
    try:
        response = llm.invoke(messages)
        return str(response.content).strip()
    except Exception as e:
        _logger.error("Error generating executive summary", exc_info=e)
        return "Executive summary not available due to generation error."


_logger = create_logger("report_generator")

# Setup paths
CURRENT_DIR = Path(__file__).parent
REPORT_DIR = Path(__file__).parent.parent.parent / "files" / "reports"


# ================================
# State definition
# ================================
class ReportGenerationState(TypedDict, total=False):
    """State dictionary for report generation process."""

    metadata: Dict[str, Any]
    analysis: Dict[str, Any]
    heuristic: Dict[str, Any]
    questionnaire: Dict[str, Any]
    html_path: str
    messages: Annotated[List[AnyMessage], add]
    errors: Annotated[List[str], add]


# ================================
# NODE 1 - Load Input
# ================================
def node_load(state: ReportGenerationState) -> ReportGenerationState:
    """
    Load input from heuristic_analyzer.

    Args:
        state (ReportGenerationState): The initial state.

    Returns:
        ReportGenerationState: The updated state with loaded data.
    """
    state["messages"] = []
    state["errors"] = []

    if state.get("analysis") is None or state.get("heuristic") is None:
        err = "Missing analysis or heuristic data in initial state"
        _logger.error(err)
        errs = state.setdefault("errors", [])
        if err not in errs:
            errs.append(err)
        return state

    if state.get("questionnaire") is None:
        _logger.warning(
            "No questionnaire present in state; some report features may be limited"
        )
        state["questionnaire"] = {}

    if state.get("metadata") is None:
        _logger.warning("No metadata present, creating default")
        state["metadata"] = {}

    _logger.info(
        "Initial state received",
        step="load",
        source="heuristic_analyzer",
        has_analysis=bool(state.get("analysis")),
        has_heuristic=bool(state.get("heuristic")),
        total_risks=state.get("heuristic", {}).get("counting", {}).get("total_risks"),
    )
    return state


# ================================
# NODE 2 - Generate HTML Report
# ================================
def node_generate_html_report(state: ReportGenerationState) -> ReportGenerationState:
    """
    Generate the executive summary and HTML dashboard.

    Args:
        state (ReportGenerationState): The current state.

    Returns:
        ReportGenerationState: The updated state with HTML report path.
    """
    try:
        # Retrieve language from metadata, default to 'en'
        meta = state.setdefault("metadata", {})
        language = meta.get("language", "en")

        # Genera executive summary e salva nei metadati
        payload = {
            "heuristic": state.get("heuristic", {}),
            "analysis": state.get("analysis", {}),
        }
        summary_text = generate_executive_summary_text(
            payload["heuristic"],
            payload["analysis"],
            language,
        )
        meta["executive_summary_text"] = summary_text

        if not state.get("questionnaire"):
            _logger.warning(
                "Questionnaire not found in state; attempting to load from file."
            )
            run_id = meta.get("run_id")
            if run_id:
                import os

                answers_path = os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "files",
                    "answers",
                    f"answers_{run_id}.json",
                )
                answers_path = os.path.abspath(answers_path)
                if os.path.isfile(answers_path):
                    try:
                        with open(answers_path, "r", encoding="utf-8") as f:
                            state["questionnaire"] = json.load(f)
                        _logger.info(f"Answers loaded from {answers_path}")
                    except Exception as e:
                        _logger.warning(
                            f"Unable to load answers from {answers_path}: {e}"
                        )
                else:
                    _logger.warning(f"Answers file not found: {answers_path}")
            else:
                _logger.warning(
                    "run_id not present in metadata: unable to load answers"
                )

        html_path = generate_html_report(
            metadata=state.get("metadata", {}),
            heuristic=state.get("heuristic", {}),
            analysis=state.get("analysis", {}),
            questionnaire=state.get("questionnaire", {}),
        )
        state["html_path"] = str(html_path)

        _logger.info(
            "HTML report generated",
            step="generate_html",
            html_path=str(html_path),
        )

    except Exception as e:
        _logger.error(
            "Failed to generate HTML report", step="generate_html", exc_info=e
        )

    return state


# ================================
# NODE 3 - Save Metadata
# ================================
def node_save(state: ReportGenerationState) -> ReportGenerationState:
    """
    Save report metadata.

    Args:
        state (ReportGenerationState): The current state.

    Returns:
        ReportGenerationState: The updated state after saving metadata."""
    try:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

        ts = time.strftime("%Y%m%d_%H%M%S")
        run_id = (state.get("metadata") or {}).get("run_id")
        if not run_id:
            raise RuntimeError(
                "Missing run_id in state; run must start from domain analyzer"
            )

        meta = dict(state.get("metadata") or {})
        # Ensure taxonomy versions for MIT taxonomies are present
        tax = dict(meta.get("taxonomy_versions") or {})
        tax.setdefault("domain", "v0.1")
        tax.setdefault("causal", "v0.1")
        meta["taxonomy_versions"] = tax
        meta.update(
            {
                "timestamp": ts,
                "analysis_current_step": "report_generation",
                "analysis_next_step": None,
                "html_report": state.get("html_path"),
                "errors": state.get("errors", []),
            }
        )

        metadata_file = REPORT_DIR / f"report_metadata_{run_id}.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        _logger.info(
            "Report metadata saved",
            step="save",
            metadata_file=str(metadata_file),
            html_report=state.get("html_path"),
        )

    except Exception as e:
        _logger.error("Failed to save metadata", step="save", exc_info=e)
        err_msg = f"Metadata save failed: {str(e)}"
        errs = state.setdefault("errors", [])
        if err_msg not in errs:
            errs.append(err_msg)

    return state


# ================================
# Graph construction
# ================================
def create_report_generator_graph():
    """
    Create and compile the LangGraph for report generation.

    Returns:
        StateGraph: The compiled report generation graph.
    """
    graph = StateGraph(ReportGenerationState)

    graph.add_node("Load", node_load)
    graph.add_node("GenerateHTMLReport", node_generate_html_report)
    graph.add_node("Save", node_save)

    graph.add_edge("Load", "GenerateHTMLReport")
    graph.add_edge("GenerateHTMLReport", "Save")

    graph.set_entry_point("Load")

    return graph.compile()


# ================================
# Standalone execution
# ================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate report from heuristic analysis file (specify only the file name)"
    )
    parser.add_argument(
        "filename", help="Heuristic analysis JSON file name (without path)"
    )
    args = parser.parse_args()

    filename = args.filename

    # Resolve the base project path and the heuristic analysis folder
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    heuristic_dir = os.path.join(repo_root, "files", "analysis", "heuristic")

    # If it's an absolute path, use it directly; otherwise, resolve it in the default folder
    input_file = (
        filename if os.path.isabs(filename) else os.path.join(heuristic_dir, filename)
    )

    if not os.path.isfile(input_file):
        _logger.error(
            f"Input file not found: {input_file}. "
            f"Ensure it exists in {heuristic_dir} or provide an absolute path."
        )
        sys.exit(2)

    # Load the heuristic analysis file
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        _logger.info(
            "Heuristic analysis file loaded",
            step="standalone",
            input_file=input_file,
        )

        # Create the report generator graph
        graph = create_report_generator_graph()

        # Initialize state from loaded data
        initial_state: ReportGenerationState = {
            "metadata": data.get("metadata", {}),
            "analysis": data.get("analysis", {}),
            "heuristic": data.get("heuristic", {}),
            "html_path": "",
            "messages": [],
            "errors": [],
        }

        # Execute the graph
        _logger.info("Starting report generation", step="standalone")
        final_state = graph.invoke(initial_state)

        if final_state.get("errors"):
            _logger.error(
                f"Report generation completed with errors: {final_state['errors']}"
            )
            sys.exit(1)
        else:
            _logger.info(
                "Report generation completed successfully",
                step="standalone",
                html_path=final_state.get("html_path"),
            )

            _logger.info("✅ REPORT GENERATION SUCCESSFUL")
            _logger.info(f"📄 HTML Report: {final_state.get('html_path')}")

            sys.exit(0)

    except json.JSONDecodeError as e:
        _logger.error(
            f"Invalid JSON file: {input_file}. Error: {e.msg}",
            exc_info=True,
        )
        sys.exit(2)
    except Exception as e:
        _logger.error(
            f"Unexpected error: {str(e)}",
            exc_info=True,
        )
        sys.exit(1)
