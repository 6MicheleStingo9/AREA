import argparse
import json
from operator import add
import os
from pathlib import Path
import sys
import time
from typing import Annotated, Any, Dict, List, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph import StateGraph
from pyswip import Prolog

from utils.utils import create_logger


_logger = create_logger("heuristic_analyzer")

# Setup paths
CURRENT_DIR = Path(__file__).parent
RULES_FILE = CURRENT_DIR / "rules.pl"
HEURISTIC_DIR = Path(__file__).parent.parent.parent / "files" / "analysis" / "heuristic"


# ================================
# State definition
# ================================
class HeuristicAnalysisState(TypedDict, total=False):
    """State dictionary for heuristic analysis process."""

    metadata: Dict[str, Any]
    analysis: Dict[str, Any]
    heuristic: Dict[str, Any]
    prolog_facts: List[str]
    prolog: Any  # Prolog instance
    messages: Annotated[List[AnyMessage], add]
    errors: Annotated[List[str], add]


# ================================
# Utility functions
# ================================
def _escape_prolog_string(s: str) -> str:
    """
    Escapes special characters in a string for Prolog.

    Args:
        s (str): The input string to escape.

    Returns:
        str: The escaped string suitable for Prolog.
    """
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "\\'")
    return s


def _extract_domain_name(domain_key: str, state: HeuristicAnalysisState) -> str:
    """
    Extracts the domain name from the MIT taxonomy.

    Args:
        domain_key (str): The domain key to extract the name for.
        state (HeuristicAnalysisState): The current state of the analysis.

    Returns:
        str: The extracted domain name.
    """
    domain_mapping = {
        "1": "Discrimination & Toxicity",
        "2": "Privacy & Security",
        "3": "Misinformation",
        "4": "Malicious actors",
        "5": "Human-Computer Interaction",
        "6": "Socioeconomic & Environmental",
        "7": "AI system safety, failures, & limitations",
    }
    return domain_mapping.get(domain_key.split(".")[0], f"Domain {domain_key}")


def _extract_subdomain_name(domain_key: str, subdomain_key: str) -> str:
    """
    Extracts the subdomain name from the MIT taxonomy.

    Args:
        domain_key (str): The domain key to extract the name for.
        subdomain_key (str): The subdomain key to extract the name for.

    Returns:
        str: The extracted subdomain name.
    """
    subdomain_mapping = {
        "1.1": "Unfair discrimination and misrepresentation",
        "1.2": "Exposure to toxic content",
        "1.3": "Unequal performance across groups",
        "2.1": "Compromise of privacy by obtaining, leaking or correctly inferring sensitive information",
        "2.2": "AI system security vulnerabilities and attacks",
        "3.1": "False or misleading information",
        "3.2": "Pollution of information ecosystem and loss of consensus reality",
        "4.1": "Disinformation, surveillance, and influence at scale",
        "4.2": "Cyberattacks, weapon development or use, and mass harm",
        "4.3": "Fraud, scams, and targeted manipulation",
        "5.1": "Overreliance and unsafe use",
        "5.2": "Loss of human agency and autonomy",
        "6.1": "Power centralization and unfair distribution of benefits",
        "6.2": "Increased inequality and decline in employment quality",
        "6.3": "Economic and cultural devaluation of human effort",
        "6.4": "Competitive dynamics",
        "6.5": "Governance failure",
        "6.6": "Environmental harm",
        "7.1": "AI pursuing its own goals in conflict with human goals or values",
        "7.2": "AI possessing dangerous capabilities",
        "7.3": "Lack of capability or robustness",
        "7.4": "Lack of transparency or interpretability",
        "7.5": "AI welfare and rights",
        "7.6": "Multi-agent risks",
    }
    full_key = f"{domain_key}.{subdomain_key}"
    return subdomain_mapping.get(full_key, f"Subdomain {full_key}")


# ================================
# NODE 1 - Load Input
# ================================
def node_load(state: HeuristicAnalysisState) -> HeuristicAnalysisState:
    """
    Loads input from the causality_analyzer.

    Args:
        state (HeuristicAnalysisState): The current state of the analysis.

    Returns:
        HeuristicAnalysisState: The updated state after loading input.
    """
    state["messages"] = []
    state["errors"] = []

    if state.get("analysis") is None:
        err = "No analysis data present in initial state"
        _logger.error(err)
        errs = state.setdefault("errors", [])
        if err not in errs:
            errs.append(err)
        return state

    if state.get("metadata") is None:
        _logger.warning("No metadata present, creating default")
        state["metadata"] = {}

    _logger.info(
        "Initial state received",
        step="load",
        source="causality_analyzer",
        has_analysis=bool(state.get("analysis")),
        domains=len(state.get("analysis", {})),
    )
    return state


# ================================
# NODE 2 - Generate Prolog Facts
# ================================
def node_generate_prolog_facts(state: HeuristicAnalysisState) -> HeuristicAnalysisState:
    """
    Generates Prolog facts from the causality analysis JSON.

    Args:
        state (HeuristicAnalysisState): The current state of the analysis.

    Returns:
        HeuristicAnalysisState: The updated state with generated Prolog facts.
    """
    analysis = state.get("analysis", {})
    facts = []

    domains_seen = set()
    subdomains_seen = set()

    try:
        for domain_subdomain, content in analysis.items():
            risks = content.get("risks", [])

            parts = domain_subdomain.split(".")
            if len(parts) != 2:
                continue

            domain, subdomain = parts

            # Add domain fact if not already seen
            if domain not in domains_seen:
                domain_name = _extract_domain_name(domain, state)
                domain_name_escaped = _escape_prolog_string(domain_name)
                facts.append(f"domain('{domain}', '{domain_name_escaped}')")
                domains_seen.add(domain)

            # Add subdomain fact if not already seen
            subdomain_key = f"{domain}.{subdomain}"
            if subdomain_key not in subdomains_seen:
                subdomain_name = _extract_subdomain_name(domain, subdomain)
                subdomain_name_escaped = _escape_prolog_string(subdomain_name)
                facts.append(
                    f"subdomain('{domain}', '{subdomain}', '{subdomain_name_escaped}')"
                )
                subdomains_seen.add(subdomain_key)

            # Generate facts for each risk
            for risk_id, risk in enumerate(risks, start=1):
                title = _escape_prolog_string(risk.get("title", ""))
                severity = risk.get("severity", "medium")

                causality = risk.get("causality", {})

                if "entity" in causality and isinstance(causality["entity"], dict):
                    entity = causality.get("entity", {}).get("value", "other")
                    intent = causality.get("intent", {}).get("value", "other")
                    timing = causality.get("timing", {}).get("value", "other")
                else:
                    entity = risk.get("entity", "other")
                    intent = risk.get("intent", "other")
                    timing = risk.get("timing", "other")

                # Risk fact
                facts.append(
                    f"risk('{domain}', '{subdomain}', {risk_id}, '{title}', {severity})"
                )

                # Causality facts
                facts.append(
                    f"causality_entity('{domain}', '{subdomain}', {risk_id}, {entity})"
                )
                facts.append(
                    f"causality_intent('{domain}', '{subdomain}', {risk_id}, {intent})"
                )
                facts.append(
                    f"causality_timing('{domain}', '{subdomain}', {risk_id}, '{timing}')"
                )

        state["prolog_facts"] = facts
        _logger.info(
            "Prolog facts generated",
            step="generate_facts",
            facts_count=len(facts),
            domains=len(domains_seen),
            subdomains=len(subdomains_seen),
        )
    except Exception as e:
        _logger.error(
            "Failed to generate Prolog facts", step="generate_facts", exc_info=e
        )
        err_msg = f"Prolog facts generation failed: {str(e)}"
        errs = state.setdefault("errors", [])
        if err_msg not in errs:
            errs.append(err_msg)

    return state


# ================================
# NODE 3 - Initialize Prolog
# ================================
def node_initialize_prolog(state: HeuristicAnalysisState) -> HeuristicAnalysisState:
    """
    Initializes Prolog, loads rules, and asserts facts.

    Args:
        state (HeuristicAnalysisState): The current state of the analysis.

    Returns:
        HeuristicAnalysisState: The updated state after initializing Prolog.
    """
    try:
        if not RULES_FILE.exists():
            raise FileNotFoundError(f"Rules file not found: {RULES_FILE}")

        prolog = Prolog()
        prolog.consult(str(RULES_FILE))

        facts = state.get("prolog_facts", [])
        for fact in facts:
            prolog.assertz(fact)

        state["prolog"] = prolog
        _logger.info(
            "Prolog initialized",
            step="initialize_prolog",
            rules_file=str(RULES_FILE),
            facts_asserted=len(facts),
        )
    except Exception as e:
        _logger.error(
            "Failed to initialize Prolog", step="initialize_prolog", exc_info=e
        )
        err_msg = f"Prolog initialization failed: {str(e)}"
        errs = state.setdefault("errors", [])
        if err_msg not in errs:
            errs.append(err_msg)
        raise RuntimeError(f"Prolog initialization failed: {e}")

    return state


# ================================
# NODE 4 - Execute Heuristic Analysis
# ================================
def node_execute_heuristic_analysis(
    state: HeuristicAnalysisState,
) -> HeuristicAnalysisState:
    """
    Executes all Prolog queries for heuristic analysis.

    Args:
        state (HeuristicAnalysisState): The current state of the analysis.

    Returns:
        HeuristicAnalysisState: The updated state after executing heuristic analysis.
    """
    prolog = state.get("prolog")
    if prolog is None:
        err = "Prolog instance not available"
        _logger.error(err)
        errs = state.setdefault("errors", [])
        if err not in errs:
            errs.append(err)
        return state

    try:
        # Executive Summary
        executive_summary = _run_executive_summary(prolog)

        # Counting
        counting_results = _run_basic_counting_analysis(prolog)

        # Patterns
        pattern_results = _run_pattern_analysis(prolog)

        # Context
        context_results = _run_context_analysis(prolog)

        # Combina i risultati
        state["heuristic"] = {
            "executive_summary": executive_summary,
            "counting": counting_results,
            "patterns": pattern_results,
            "context": context_results,
        }

        _logger.info(
            "Heuristic analysis completed",
            step="execute_analysis",
            total_risks=counting_results.get("total_risks"),
            risk_score=executive_summary.get("global_risk_score"),
        )
    except Exception as e:
        _logger.error(
            "Failed to execute heuristic analysis", step="execute_analysis", exc_info=e
        )
        err_msg = f"Heuristic analysis failed: {str(e)}"
        errs = state.setdefault("errors", [])
        if err_msg not in errs:
            errs.append(err_msg)
        raise RuntimeError(f"Heuristic analysis failed: {e}")

    return state


def _run_executive_summary(prolog: Prolog) -> Dict[str, Any]:
    """
    Run executive summary queries.

    Args:
        prolog (Prolog): The Prolog instance to run queries on.

    Returns:
        Dict[str, Any]: The results of the executive summary queries.
    """
    results = {}

    # Global Risk Score
    try:
        score = list(prolog.query("global_risk_score(S)"))[0]["S"]
        results["global_risk_score"] = round(score, 2)
    except Exception:
        results["global_risk_score"] = None

    # Overall Risk Level
    try:
        level = list(prolog.query("overall_risk_level(L)"))[0]["L"]
        results["overall_risk_level"] = level
    except Exception:
        results["overall_risk_level"] = None

    # Primary Concern
    try:
        concern = list(prolog.query("primary_concern(C)"))[0]["C"]
        results["primary_concern"] = concern
    except Exception:
        results["primary_concern"] = None

    # Recommended Action
    try:
        action = list(prolog.query("recommended_action(A)"))[0]["A"]
        results["recommended_action"] = action
    except Exception:
        results["recommended_action"] = None

    # Most Critical Domain
    try:
        most_critical = list(prolog.query("most_critical_domain(D, N, C)"))
        if most_critical:
            domain = most_critical[0]["D"]
            domain_name = most_critical[0]["N"]
            count = most_critical[0]["C"]

            # Get most critical subdomain within this domain
            most_critical_subdomain = None
            try:
                subdomain_query = list(
                    prolog.query("most_critical_subdomain_in_top_domain(D, SD, SDN, C)")
                )
                if subdomain_query:
                    most_critical_subdomain = {
                        "subdomain": subdomain_query[0]["SD"],
                        "subdomain_name": subdomain_query[0]["SDN"],
                        "high_count": subdomain_query[0]["C"],
                    }
            except Exception:
                pass

            results["most_critical_domain"] = {
                "domain": domain,
                "domain_name": domain_name,
                "high_count": count,
                "most_critical_subdomain": most_critical_subdomain,
            }
        else:
            results["most_critical_domain"] = None
    except Exception:
        results["most_critical_domain"] = None

    # Top 3 Critical Domains
    try:
        top_domains = []
        for rank in range(1, 4):
            result = list(prolog.query(f"critical_domain_ranked({rank}, D, N, C)"))
            if result:
                domain = result[0]["D"]
                domain_name = result[0]["N"]
                count = result[0]["C"]
                top_domains.append(
                    {
                        "rank": rank,
                        "domain": domain,
                        "domain_name": domain_name,
                        "high_count": count,
                    }
                )

        results["top_3_critical_domains"] = top_domains
    except Exception:
        results["top_3_critical_domains"] = []

    return results


def _run_basic_counting_analysis(prolog: Prolog) -> Dict[str, Any]:
    """
    Runs basic counting analysis queries.

    Args:
        prolog (Prolog): The Prolog instance to run queries on.

    Returns:
        Dict[str, Any]: The results of the basic counting analysis queries.
    """
    results = {}

    # Total risks
    try:
        total = list(prolog.query("total_risks(Count)"))[0]["Count"]
        results["total_risks"] = total
    except Exception:
        results["total_risks"] = None

    # Risks by severity
    results["by_severity"] = {}
    for severity in ["low", "medium", "high"]:
        try:
            count = list(prolog.query(f"risks_by_severity({severity}, Count)"))[0][
                "Count"
            ]
            results["by_severity"][severity] = count
        except Exception:
            results["by_severity"][severity] = None

    # Risks by entity
    results["by_entity"] = {}
    for entity in ["ai", "human", "other"]:
        try:
            count = list(prolog.query(f"risks_by_entity({entity}, Count)"))[0]["Count"]
            results["by_entity"][entity] = count
        except Exception:
            results["by_entity"][entity] = None

    # Risks by intent
    results["by_intent"] = {}
    for intent in ["intentional", "unintentional", "other"]:
        try:
            count = list(prolog.query(f"risks_by_intent({intent}, Count)"))[0]["Count"]
            results["by_intent"][intent] = count
        except Exception:
            results["by_intent"][intent] = None

    # Risks by timing
    results["by_timing"] = {}
    for timing in ["pre-deployment", "post-deployment", "other"]:
        try:
            query_str = f"risks_by_timing('{timing}', Count)"
            count = list(prolog.query(query_str))[0]["Count"]
            results["by_timing"][timing] = count
        except Exception:
            results["by_timing"][timing] = None

    # Risks by domain
    results["by_domain"] = {}
    try:
        domains = list(prolog.query("domain(D, _)"))
        for domain_result in domains:
            domain_id = domain_result["D"]
            try:
                count = list(prolog.query(f"risks_in_domain('{domain_id}', Count)"))[0][
                    "Count"
                ]
                results["by_domain"][domain_id] = count
            except Exception:
                results["by_domain"][domain_id] = None
    except Exception:
        pass

    return results


def _run_pattern_analysis(prolog: Prolog) -> Dict[str, Any]:
    """
    Runs analysis of critical patterns and combinations.

    Args:
        prolog (Prolog): The Prolog instance to run queries on.

    Returns:
        Dict[str, Any]: The results of the pattern analysis queries.
    """
    results = {}

    # Critical Patterns
    results["critical_patterns"] = {}

    try:
        count = list(prolog.query("critical_ai_risks_count(Count)"))[0]["Count"]
        results["critical_patterns"]["critical_ai_risks"] = count
    except Exception:
        results["critical_patterns"]["critical_ai_risks"] = None

    try:
        count = list(prolog.query("malicious_human_risks_count(Count)"))[0]["Count"]
        results["critical_patterns"]["malicious_human_risks"] = count
    except Exception:
        results["critical_patterns"]["malicious_human_risks"] = None

    try:
        count = list(prolog.query("high_threat_attacks_count(Count)"))[0]["Count"]
        results["critical_patterns"]["high_threat_attacks"] = count
    except Exception:
        results["critical_patterns"]["high_threat_attacks"] = None

    try:
        count = list(prolog.query("unintended_ai_failures_count(Count)"))[0]["Count"]
        results["critical_patterns"]["unintended_ai_failures"] = count
    except Exception:
        results["critical_patterns"]["unintended_ai_failures"] = None

    try:
        count = list(prolog.query("human_error_risks_count(Count)"))[0]["Count"]
        results["critical_patterns"]["human_error_risks"] = count
    except Exception:
        results["critical_patterns"]["human_error_risks"] = None

    try:
        count = list(prolog.query("intentional_ai_risks_count(Count)"))[0]["Count"]
        results["critical_patterns"]["intentional_ai_risks"] = count
    except Exception:
        results["critical_patterns"]["intentional_ai_risks"] = None

    try:
        count = list(prolog.query("preventable_critical_ai_risks_count(Count)"))[0][
            "Count"
        ]
        results["critical_patterns"]["preventable_critical_ai_risks"] = count
    except Exception:
        results["critical_patterns"]["preventable_critical_ai_risks"] = None

    try:
        count = list(prolog.query("critical_human_errors_count(Count)"))[0]["Count"]
        results["critical_patterns"]["critical_human_errors"] = count
    except Exception:
        results["critical_patterns"]["critical_human_errors"] = None

    try:
        count = list(prolog.query("low_priority_preventable_count(Count)"))[0]["Count"]
        results["critical_patterns"]["low_priority_preventable"] = count
    except Exception:
        results["critical_patterns"]["low_priority_preventable"] = None

    # Moderate Patterns
    results["moderate_patterns"] = {}

    try:
        count = list(prolog.query("moderate_operational_risks_count(Count)"))[0][
            "Count"
        ]
        results["moderate_patterns"]["moderate_operational_risks"] = count
    except Exception:
        results["moderate_patterns"]["moderate_operational_risks"] = None

    try:
        count = list(prolog.query("moderate_ai_risks_count(Count)"))[0]["Count"]
        results["moderate_patterns"]["moderate_ai_risks"] = count
    except Exception:
        results["moderate_patterns"]["moderate_ai_risks"] = None

    try:
        count = list(prolog.query("moderate_human_risks_count(Count)"))[0]["Count"]
        results["moderate_patterns"]["moderate_human_risks"] = count
    except Exception:
        results["moderate_patterns"]["moderate_human_risks"] = None

    try:
        count = list(prolog.query("moderate_intentional_ai_risks_count(Count)"))[0][
            "Count"
        ]
        results["moderate_patterns"]["moderate_intentional_ai_risks"] = count
    except Exception:
        results["moderate_patterns"]["moderate_intentional_ai_risks"] = None

    try:
        count = list(prolog.query("moderate_human_intentional_risks_count(Count)"))[0][
            "Count"
        ]
        results["moderate_patterns"]["moderate_human_intentional_risks"] = count
    except Exception:
        results["moderate_patterns"]["moderate_human_intentional_risks"] = None

    # Prevention Patterns
    results["prevention_patterns"] = {}

    try:
        count = list(prolog.query("preventable_ai_risks_count(Count)"))[0]["Count"]
        results["prevention_patterns"]["preventable_ai_risks"] = count
    except Exception:
        results["prevention_patterns"]["preventable_ai_risks"] = None

    try:
        count = list(prolog.query("preventable_human_risks_count(Count)"))[0]["Count"]
        results["prevention_patterns"]["preventable_human_risks"] = count
    except Exception:
        results["prevention_patterns"]["preventable_human_risks"] = None

    try:
        count = list(prolog.query("preventable_intentional_threats_count(Count)"))[0][
            "Count"
        ]
        results["prevention_patterns"]["preventable_intentional_threats"] = count
    except Exception:
        results["prevention_patterns"]["preventable_intentional_threats"] = None

    # Minor Patterns
    results["low_patterns"] = {}

    try:
        count = list(prolog.query("low_operational_risks_count(Count)"))[0]["Count"]
        results["low_patterns"]["low_operational_risks"] = count
    except Exception:
        results["low_patterns"]["low_operational_risks"] = None

    # Subdomain Analysis
    results["subdomain_analysis"] = {}

    try:
        most_critical = list(
            prolog.query("most_critical_subdomain(D, SD, Name, Count)")
        )
        if most_critical:
            result = most_critical[0]
            domain = result["D"]
            subdomain = result["SD"]
            subdomain_name = result["Name"]
            count = result["Count"]

            results["subdomain_analysis"]["most_critical"] = {
                "subdomain": f"{domain}.{subdomain}",
                "subdomain_name": subdomain_name,
                "high_risk_count": count,
            }
        else:
            results["subdomain_analysis"]["most_critical"] = None
    except Exception:
        results["subdomain_analysis"]["most_critical"] = None

    # Most critical subdomain in the most critical domain
    try:
        in_top_domain = list(
            prolog.query("most_critical_subdomain_in_top_domain(D, SD, Name, Count)")
        )
        if in_top_domain:
            result = in_top_domain[0]
            domain = result["D"]
            subdomain = result["SD"]
            subdomain_name = result["Name"]
            count = result["Count"]

            results["subdomain_analysis"]["most_critical_in_top_domain"] = {
                "subdomain": f"{domain}.{subdomain}",
                "subdomain_name": subdomain_name,
                "high_risk_count": count,
            }
    except Exception:
        results["subdomain_analysis"]["most_critical_in_top_domain"] = None

    # Distribution Metrics
    results["distribution_metrics"] = {}

    try:
        percentage = list(prolog.query("percentage_ai_predeployment(P)"))[0]["P"]
        results["distribution_metrics"]["ai_predeployment_percentage"] = round(
            percentage, 2
        )
    except Exception:
        results["distribution_metrics"]["ai_predeployment_percentage"] = None

    try:
        percentage = list(prolog.query("percentage_high_intentional(P)"))[0]["P"]
        results["distribution_metrics"]["high_intentional_percentage"] = round(
            percentage, 2
        )
    except Exception:
        results["distribution_metrics"]["high_intentional_percentage"] = None

    try:
        ratio = list(prolog.query("ai_human_ratio(R)"))[0]["R"]
        results["distribution_metrics"]["ai_human_ratio"] = round(ratio, 2)
    except Exception:
        results["distribution_metrics"]["ai_human_ratio"] = None

    # Alert Indicators
    results["alerts"] = {}

    # Critical HIGH Concentration
    try:
        high_pct_query = list(prolog.query("percentage_high_severity(P)"))
        high_pct = high_pct_query[0]["P"] if high_pct_query else 0
        has_critical = high_pct > 40
        results["alerts"]["critical_risk_concentration"] = {
            "alert": has_critical,
            "value": round(high_pct, 2),
        }
    except Exception:
        results["alerts"]["critical_risk_concentration"] = None

    # AI Dominance
    try:
        ai_count = list(prolog.query("risks_by_entity(ai, C)"))[0]["C"]
        total = list(prolog.query("total_risks(T)"))[0]["T"]
        ai_pct = (ai_count / total * 100) if total > 0 else 0
        has_dominance = ai_pct > 60
        results["alerts"]["ai_dominance"] = {
            "alert": has_dominance,
            "value": round(ai_pct, 2),
        }
    except Exception:
        results["alerts"]["ai_dominance"] = None

    # Intentional Threats
    try:
        intent_count = list(prolog.query("risks_by_intent(intentional, C)"))[0]["C"]
        has_threats = intent_count > 3
        results["alerts"]["intentional_threats"] = {
            "alert": has_threats,
            "value": intent_count,
        }
    except Exception:
        results["alerts"]["intentional_threats"] = None

    # Operational Risks
    try:
        post_count = list(prolog.query("risks_by_timing('post-deployment', C)"))[0]["C"]
        total = list(prolog.query("total_risks(T)"))[0]["T"]
        post_pct = (post_count / total * 100) if total > 0 else 0
        has_operational = post_pct > 70
        results["alerts"]["operational_risks"] = {
            "alert": has_operational,
            "value": round(post_pct, 2),
        }
    except Exception:
        results["alerts"]["operational_risks"] = None

    # Preventable Risks
    try:
        pre_count = list(prolog.query("risks_by_timing('pre-deployment', C)"))[0]["C"]
        total = list(prolog.query("total_risks(T)"))[0]["T"]
        pre_pct = (pre_count / total * 100) if total > 0 else 0
        low_preventable = pre_pct < 10
        results["alerts"]["low_preventable_ratio"] = {
            "alert": low_preventable,
            "value": round(pre_pct, 2),
        }
    except Exception:
        results["alerts"]["low_preventable_ratio"] = None

    # Moderate Risk Accumulation
    try:
        medium_count = list(prolog.query("risks_by_severity(medium, C)"))[0]["C"]
        total = list(prolog.query("total_risks(T)"))[0]["T"]
        medium_pct = (medium_count / total * 100) if total > 0 else 0
        has_medium = medium_pct > 40
        results["alerts"]["medium_risk_accumulation"] = {
            "alert": has_medium,
            "value": round(medium_pct, 2),
        }
    except Exception:
        results["alerts"]["medium_risk_accumulation"] = None

    # Human Error Dominance
    try:
        human_count = list(prolog.query("risks_by_entity(human, C)"))[0]["C"]
        total = list(prolog.query("total_risks(T)"))[0]["T"]
        human_pct = (human_count / total * 100) if total > 0 else 0
        has_human_dom = human_pct > 50
        results["alerts"]["human_error_dominance"] = {
            "alert": has_human_dom,
            "value": round(human_pct, 2),
        }
    except Exception:
        results["alerts"]["human_error_dominance"] = None

    # High Risk Fragmentation
    try:
        domains_with_high_query = list(
            prolog.query("risks_in_domain_by_severity(D, high, C), C > 0")
        )
        domain_count = len(set([d["D"] for d in domains_with_high_query]))
        high_count = list(prolog.query("risks_by_severity(high, C)"))[0]["C"]
        is_fragmented = domain_count >= 4 and high_count >= 6
        results["alerts"]["high_risk_fragmentation"] = {
            "alert": is_fragmented,
            "value": domain_count,
        }
    except Exception:
        results["alerts"]["high_risk_fragmentation"] = None

    return results


def _run_context_analysis(prolog: Prolog) -> Dict[str, Any]:
    """
    Runs analysis of context and comparison queries.

    Args:
        prolog (Prolog): The Prolog instance to run queries on.

    Returns:
        Dict[str, Any]: The results of the context analysis queries.
    """
    results = {}

    # Risk Profile Comparison
    try:
        comparison = list(prolog.query("risk_profile_comparison(C)"))[0]["C"]
        results["risk_profile_comparison"] = comparison
    except Exception:
        results["risk_profile_comparison"] = None

    # Dominant Pattern
    try:
        dominant = list(prolog.query("dominant_pattern(E, I, T, C)"))
        if dominant:
            entity = dominant[0]["E"]
            intent = dominant[0]["I"]
            timing = dominant[0]["T"]
            count = dominant[0]["C"]
            results["dominant_pattern"] = {
                "entity": entity,
                "intent": intent,
                "timing": timing,
                "count": count,
            }
        else:
            results["dominant_pattern"] = None
    except Exception:
        results["dominant_pattern"] = None

    # Fully Defined Causality Percentage
    try:
        percentage = list(prolog.query("fully_defined_causality_percentage(P)"))[0]["P"]
        results["fully_defined_causality_percentage"] = round(percentage, 2)
    except Exception:
        results["fully_defined_causality_percentage"] = None

    # Domain Coverage
    try:
        percentage = list(prolog.query("domain_coverage_percentage(P)"))[0]["P"]
        results["domain_coverage_percentage"] = round(percentage, 2)
    except Exception:
        results["domain_coverage_percentage"] = None

    # Subdomain Coverage
    try:
        percentage = list(prolog.query("subdomain_coverage_percentage(P)"))[0]["P"]
        results["subdomain_coverage_percentage"] = round(percentage, 2)
    except Exception:
        results["subdomain_coverage_percentage"] = None

    return results


# ================================
# NODE 5 - Save Output
# ================================
def node_save(state: HeuristicAnalysisState) -> HeuristicAnalysisState:
    """
    Save the complete output in JSON.

    Args:
        state (HeuristicAnalysisState): The current state of the analysis.

    Returns:
        HeuristicAnalysisState: The updated state after saving output.
    """
    try:
        os.makedirs(HEURISTIC_DIR, exist_ok=True)

        ts = time.strftime("%Y%m%d_%H%M%S")
        run_id = (state.get("metadata") or {}).get("run_id")
        if not run_id:
            raise RuntimeError(
                "Missing run_id in state; run must start from domain analyzer"
            )
        filename = f"heuristic_analysis_{run_id}.json"
        path = HEURISTIC_DIR / filename

        meta = dict(state.get("metadata") or {})
        meta.update(
            {
                "timestamp": ts,
                "analysis_current_step": "heuristic_evaluation",
                "analysis_next_step": "report_generation",
                "errors": state.get("errors", []),
            }
        )

        payload = {
            "metadata": meta,
            "analysis": state.get("analysis"),
            "heuristic": state.get("heuristic"),
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        _logger.info(
            "Heuristic analysis saved",
            step="save",
            output_path=str(path),
            total_risks=state.get("heuristic", {})
            .get("counting", {})
            .get("total_risks"),
            risk_score=state.get("heuristic", {})
            .get("executive_summary", {})
            .get("global_risk_score"),
        )
    except Exception as e:
        _logger.error("Failed saving heuristic analysis", step="save", exc_info=e)
        err_msg = f"Save failed: {str(e)}"
        errs = state.setdefault("errors", [])
        if err_msg not in errs:
            errs.append(err_msg)

    return state


# ================================
# Graph construction
# ================================
def create_heuristic_analyzer_graph():
    """
    Create and compile the LangGraph graph for heuristic analysis.

    Returns:
        CompiledGraph: The compiled graph ready for invocation.
    """
    graph = StateGraph(HeuristicAnalysisState)

    graph.add_node("Load", node_load)
    graph.add_node("GeneratePrologFacts", node_generate_prolog_facts)
    graph.add_node("InitializeProlog", node_initialize_prolog)
    graph.add_node("ExecuteHeuristicAnalysis", node_execute_heuristic_analysis)
    graph.add_node("Save", node_save)

    graph.add_edge("Load", "GeneratePrologFacts")
    graph.add_edge("GeneratePrologFacts", "InitializeProlog")
    graph.add_edge("InitializeProlog", "ExecuteHeuristicAnalysis")
    graph.add_edge("ExecuteHeuristicAnalysis", "Save")

    graph.set_entry_point("Load")

    return graph.compile()


# ================================
# Standalone execution
# ================================
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate heuristic analysis from causality analysis file"
    )
    parser.add_argument(
        "filename",
        help="Causality analysis JSON file name (without path) or absolute path",
    )
    args = parser.parse_args()

    filename = args.filename

    # Resolve path
    if Path(filename).is_absolute():
        input_file = Path(filename)
    else:
        repo_root = Path(__file__).parent.parent.parent
        causality_dir = repo_root / "files" / "analysis" / "causality"
        input_file = causality_dir / filename

    if not input_file.exists():
        _logger.error(
            f"Input file not found: {input_file}",
            step="standalone",
        )
        sys.exit(2)

    # Load causality analysis file
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        _logger.info(
            "Causality analysis file loaded",
            step="standalone",
            input_file=str(input_file),
        )

        # Create the heuristic analyzer graph
        graph = create_heuristic_analyzer_graph()

        # Initialize state from loaded data
        initial_state: HeuristicAnalysisState = {
            "metadata": data.get("metadata", {}),
            "analysis": data.get("analysis", {}),
            "heuristic": {},
            "prolog_facts": "",
            "messages": [],
            "errors": [],
        }

        # Execute the graph
        _logger.info("Starting heuristic analysis", step="standalone")
        final_state = graph.invoke(initial_state)

        if final_state.get("errors"):
            _logger.error(
                f"Heuristic analysis completed with errors: {final_state['errors']}",
                step="standalone",
            )
            sys.exit(1)
        else:
            heuristic = final_state.get("heuristic", {})
            exec_summary = heuristic.get("executive_summary", {})
            counting = heuristic.get("counting", {})
            most_critical = exec_summary.get("most_critical_domain", {})

            _logger.info(
                "Heuristic analysis completed successfully",
                step="standalone",
                total_risks=counting.get("total_risks"),
                risk_score=exec_summary.get("global_risk_score"),
                risk_level=exec_summary.get("overall_risk_level"),
                critical_domain=most_critical.get("domain_name"),
                critical_subdomain=most_critical.get("most_critical_subdomain", {}).get(
                    "subdomain_name"
                ),
            )

            _logger.info(
                "✅ HEURISTIC ANALYSIS SUCCESSFUL",
                total_risks=counting.get("total_risks"),
                risk_score=exec_summary.get("global_risk_score"),
                risk_level=(exec_summary.get("overall_risk_level") or "").upper(),
                critical_domain=most_critical.get("domain_name", "N/A"),
                critical_subdomain=(
                    most_critical.get("most_critical_subdomain", {}) or {}
                ).get("subdomain_name", "N/A"),
            )
            sys.exit(0)

    except json.JSONDecodeError as e:
        _logger.error(
            f"Invalid JSON file: {input_file}. Error: {e.msg}",
            step="standalone",
            exc_info=True,
        )
        sys.exit(2)
    except Exception as e:
        _logger.error(
            f"Unexpected error: {str(e)}",
            step="standalone",
            exc_info=True,
        )
        sys.exit(1)
