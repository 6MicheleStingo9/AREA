import argparse
import os
import sys
from typing import TypedDict, Dict, Any

from langgraph.graph import StateGraph, END

from agents.causality_analyzer.causality_risk_analyzer_agent import (
    create_causality_analyzer_graph,
)
from agents.domain_analyzer.domain_risk_analyzer_agent import (
    create_domain_analyzer_graph,
)
from agents.heuristic_analyzer.heuristic_risk_analyzer_agent import (
    create_heuristic_analyzer_graph,
)
from agents.report_generator.report_generator_agent import (
    create_report_generator_graph,
)
from utils.utils import create_logger


_logger = create_logger("orchestrator")


class OrchestratorState(TypedDict, total=False):
    """State structure for the orchestrator graph."""

    input_file: str
    domain_state: Dict[str, Any]
    causality_state: Dict[str, Any]
    heuristic_state: Dict[str, Any]
    report_state: Dict[str, Any]


def domain_step(state: OrchestratorState) -> OrchestratorState:
    """
    Perform domain analysis step.

    Args:
        state (OrchestratorState): The current state of the orchestrator.

    Returns:
        OrchestratorState: The updated state after domain analysis.
    """
    _logger.info(
        "Domain analysis start", step="orchestrator", input_file=state["input_file"]
    )
    graph = create_domain_analyzer_graph(state["input_file"])
    result = graph.invoke(state["domain_state"])
    if result.get("errors"):
        raise Exception(f"Domain analysis failed: {result['errors']}")
    state["domain_state"] = result
    return state


def causality_step(state: OrchestratorState) -> OrchestratorState:
    """
    Perform causality analysis step.

    Args:
        state (OrchestratorState): The current state of the orchestrator.

    Returns:
        OrchestratorState: The updated state after causality analysis.
    """
    _logger.info("Causality analysis start", step="orchestrator")
    graph = create_causality_analyzer_graph()
    causality_state = {
        "metadata": state["domain_state"].get("metadata", {}),
        "questionnaire": state["domain_state"].get("questionnaire", {}),
        "analysis": state["domain_state"].get("analysis", {}),
        "messages": [],
        "errors": [],
    }
    result = graph.invoke(causality_state)
    if result.get("errors"):
        raise Exception(f"Causality analysis failed: {result['errors']}")
    state["causality_state"] = result
    return state


def heuristic_step(state: OrchestratorState) -> OrchestratorState:
    """
    Perform heuristic analysis step.

    Args:
        state (OrchestratorState): The current state of the orchestrator.

    Returns:
        OrchestratorState: The updated state after heuristic analysis.
    """
    _logger.info("Heuristic analysis start", step="orchestrator")
    graph = create_heuristic_analyzer_graph()
    heuristic_state = {
        "metadata": state["causality_state"].get("metadata", {}),
        "analysis": state["causality_state"].get("analysis", {}),
        "heuristic": {},
        "prolog_facts": [],
        "prolog": None,
        "messages": [],
        "errors": [],
    }
    result = graph.invoke(heuristic_state)
    if result.get("errors"):
        raise Exception(f"Heuristic analysis failed: {result['errors']}")
    state["heuristic_state"] = result
    return state


def report_step(state: OrchestratorState) -> OrchestratorState:
    """
    Perform report generation step.

    Args:
        state (OrchestratorState): The current state of the orchestrator.

    Returns:
        OrchestratorState: The updated state after report generation.
    """
    _logger.info("Report generation start", step="orchestrator")
    graph = create_report_generator_graph()
    report_state = {
        "metadata": state["heuristic_state"].get("metadata", {}),
        "analysis": state["heuristic_state"].get("analysis", {}),
        "heuristic": state["heuristic_state"].get("heuristic", {}),
        "questionnaire": state["causality_state"].get("questionnaire", {}),
        "visualizations": {},
        "html_path": "",
        "messages": [],
        "errors": [],
    }
    result = graph.invoke(report_state)
    if result.get("errors"):
        raise Exception(f"Report generation failed: {result['errors']}")
    state["report_state"] = result
    return state


def build_orchestrator_graph():
    """
    Build the orchestrator graph connecting all analysis steps.

    Returns:
        StateGraph: The compiled orchestrator graph.
    """
    graph = StateGraph(OrchestratorState)
    graph.add_node("domain", domain_step)
    graph.add_node("causality", causality_step)
    graph.add_node("heuristic", heuristic_step)
    graph.add_node("report", report_step)
    graph.add_edge("domain", "causality")
    graph.add_edge("causality", "heuristic")
    graph.add_edge("heuristic", "report")
    graph.add_edge("report", END)
    graph.set_entry_point("domain")
    return graph.compile()


def run_orchestrator(input_file: str):
    """
    Run the orchestrator pipeline on the given input file.

    Args:
        input_file (str): Path to the questionnaire JSON file.

    Returns:
        Dict: The final orchestrator state (including report path).

    Raises:
        Exception: If any step fails.
    """
    if not os.path.isfile(input_file):
        _logger.error(
            "Input file not found",
            step="orchestrator",
            input_file=input_file,
        )
        raise FileNotFoundError(f"Input file not found: {input_file}")

    state = {
        "input_file": input_file,
        "domain_state": {
            "metadata": {},
            "questionnaire": {},
            "analysis": {},
            "messages": [],
            "errors": [],
        },
    }
    orchestrator = build_orchestrator_graph()
    final_state = orchestrator.invoke(state)
    _logger.info("Orchestrator completed successfully", step="orchestrator")
    _logger.info(
        "Report generation end",
        step="orchestrator",
        html_report=final_state["report_state"].get("html_path"),
    )
    return final_state


def _standaloneExecution():
    """
    Main function to run the orchestrator in standalone mode.
    """
    parser = argparse.ArgumentParser(
        description="Run analysis on a questionnaire JSON file (specify only the file name)"
    )
    parser.add_argument("filename", help="Questionnaire JSON file name (no path)")
    args = parser.parse_args()

    filename = args.filename
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    base_input_dir = os.path.join(repo_root, "area", "files", "answers")
    input_file = (
        filename if os.path.isabs(filename) else os.path.join(base_input_dir, filename)
    )

    if not os.path.isfile(input_file):
        _logger.error(
            "Input file not found",
            step="orchestrator",
            input_file=input_file,
            base_input_dir=base_input_dir,
        )
        sys.exit(2)

    # Stato iniziale
    state = {
        "input_file": input_file,
        "domain_state": {
            "metadata": {},
            "questionnaire": {},
            "analysis": {},
            "messages": [],
            "errors": [],
        },
    }

    orchestrator = build_orchestrator_graph()
    try:
        final_state = orchestrator.invoke(state)
        _logger.info("Orchestrator completed successfully", step="orchestrator")
        _logger.info(
            "Report generation end",
            step="orchestrator",
            html_report=final_state["report_state"].get("html_path"),
        )
        sys.exit(0)
    except Exception as e:
        _logger.error(str(e), step="orchestrator")
        sys.exit(1)


if __name__ == "__main__":
    _standaloneExecution()
