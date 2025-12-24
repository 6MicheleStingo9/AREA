"""
Chart Data Builder
Prepares data structures for Plotly visualizations
"""

from typing import Dict, Any


def prepare_chart_data(
    heuristic: Dict[str, Any], analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Prepare data structure for all Plotly charts.

    Args:
        heuristic (Dict[str, Any]): The heuristic analysis data.
        analysis (Dict[str, Any]): The detailed risk analysis data.

    Returns:
        Dict[str, Any]: A dictionary containing data for all charts.
    """
    return {
        "risk_distribution": build_risk_distribution_data(analysis),
        "alert_criticality": build_alert_criticality_data(heuristic),
        "causality_sankey": build_causality_sankey_data(heuristic, analysis),
        "patterns_heatmap": build_patterns_heatmap_data(heuristic),
    }


def build_risk_distribution_data(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build data for Risk Distribution stacked bar chart.

    Args:
        analysis (Dict[str, Any]): The detailed risk analysis data.

    Returns:
        Dict[str, Any]: The risk distribution data structure.
    """
    domain_names = {
        "1": "Discrimination & Toxicity",
        "2": "Privacy & Security",
        "3": "Misinformation",
        "4": "Malicious Actors",
        "5": "Human-Computer Interaction",
        "6": "Socioeconomic & Environmental",
        "7": "AI System Safety",
    }

    domains = ["1", "2", "3", "4", "5", "6", "7"]
    risk_distribution = {
        "domains": [f"D{d}" for d in domains],
        "domain_names": [domain_names[d] for d in domains],
        "high": [],
        "medium": [],
        "low": [],
    }

    # Count risks by severity for each domain
    for domain_id in domains:
        high_count = 0
        medium_count = 0
        low_count = 0

        for subdomain_id, subdomain_data in analysis.items():
            if subdomain_id.startswith(domain_id + "."):
                for risk in subdomain_data.get("risks", []):
                    severity = risk.get("severity", "").lower()
                    if severity == "high":
                        high_count += 1
                    elif severity == "medium":
                        medium_count += 1
                    elif severity == "low":
                        low_count += 1

        risk_distribution["high"].append(high_count)
        risk_distribution["medium"].append(medium_count)
        risk_distribution["low"].append(low_count)

    return risk_distribution


def build_alert_criticality_data(heuristic: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build data for Alert Criticality Radar chart (4 dimensions + 4 safety dimensions).

    Args:
        heuristic (Dict[str, Any]): The heuristic analysis data.

    Returns:
        Dict[str, Any]: The alert criticality data structure.
    """
    counting = heuristic.get("counting", {})
    total = counting.get("total_risks", 1)

    # CRITICALITY PROFILE (RED)
    # 1. Risk Concentration: % HIGH risks
    high_count = counting.get("by_severity", {}).get("high", 0)
    risk_concentration = (high_count / total * 100) if total > 0 else 0

    # 2. Operational Exposure: % post-deployment risks
    post_count = counting.get("by_timing", {}).get("post-deployment", 0)
    operational_exposure = (post_count / total * 100) if total > 0 else 0

    # 3. Threat Intensity: % intentional risks
    intentional_count = counting.get("by_intent", {}).get("intentional", 0)
    threat_intensity = (intentional_count / total * 100) if total > 0 else 0

    # 4. Prevention Deficit: 100% - % preventable risks
    pre_count = counting.get("by_timing", {}).get("pre-deployment", 0)
    prevention_ratio = (pre_count / total * 100) if total > 0 else 0
    prevention_deficit = 100 - prevention_ratio

    # SAFETY PROFILE (GREEN/BLUE)
    # 1. Impact Control: % LOW+MEDIUM risks (opposite of Risk Concentration)
    low_count = counting.get("by_severity", {}).get("low", 0)
    medium_count = counting.get("by_severity", {}).get("medium", 0)
    impact_control = ((low_count + medium_count) / total * 100) if total > 0 else 0

    # 2. Preventability: % pre-deployment risks (opposite of Operational Exposure)
    preventability = prevention_ratio

    # 3. Safety Culture: % unintentional risks (opposite of Threat Intensity)
    unintentional_count = counting.get("by_intent", {}).get("unintentional", 0)
    safety_culture = (unintentional_count / total * 100) if total > 0 else 0

    # 4. Human Oversight: % human entity risks
    human_count = counting.get("by_entity", {}).get("human", 0)
    human_oversight = (human_count / total * 100) if total > 0 else 0

    return {
        "labels": [
            "Risk Concentration",
            "Operational Exposure",
            "Threat Intensity",
            "Prevention Deficit",
        ],
        "criticality_values": [
            round(risk_concentration, 1),
            round(operational_exposure, 1),
            round(threat_intensity, 1),
            round(prevention_deficit, 1),
        ],
        "safety_labels": [
            "Impact Control",
            "Preventability",
            "Safety Culture",
            "Human Oversight",
        ],
        "safety_values": [
            round(impact_control, 1),
            round(preventability, 1),
            round(safety_culture, 1),
            round(human_oversight, 1),
        ],
    }


def build_causality_sankey_data(
    heuristic: Dict[str, Any], analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build data for Causality Flow Sankey Diagram (Entity -> Intent -> Timing).

    Args:
        heuristic (Dict[str, Any]): The heuristic analysis data.
        analysis (Dict[str, Any]): The detailed risk analysis data.

    Returns:
        Dict[str, Any]: The causality sankey data structure.
    """
    # Define nodes
    nodes = [
        "AI",
        "Human",
        "Other",  # Entity nodes (0, 1, 2)
        "Intentional",
        "Unintentional",
        "Other Intent",  # Intent nodes (3, 4, 5)
        "Pre-deployment",
        "Post-deployment",
        "Other Timing",  # Timing nodes (6, 7, 8)
    ]

    # Count flows: (entity, intent) and (intent, timing)
    entity_to_intent = {}
    intent_to_timing = {}

    for subdomain_key, subdomain_data in analysis.items():
        for risk in subdomain_data.get("risks", []):
            causality = risk.get("causality", {})

            entity = causality.get("entity", {}).get("value", "other").capitalize()
            if entity not in ["Ai", "Human", "Other"]:
                entity = "Other"
            if entity == "Ai":
                entity = "AI"

            intent = causality.get("intent", {}).get("value", "other").capitalize()
            if intent not in ["Intentional", "Unintentional", "Other"]:
                intent = "Other Intent"
            if intent == "Other":
                intent = "Other Intent"

            timing_value = causality.get("timing", {}).get("value", "other").lower()
            if timing_value == "pre-deployment":
                timing = "Pre-deployment"
            elif timing_value == "post-deployment":
                timing = "Post-deployment"
            else:
                timing = "Other Timing"

            # Count Entity -> Intent
            key1 = (entity, intent)
            entity_to_intent[key1] = entity_to_intent.get(key1, 0) + 1

            # Count Intent -> Timing
            key2 = (intent, timing)
            intent_to_timing[key2] = intent_to_timing.get(key2, 0) + 1

    # Build links
    sources = []
    targets = []
    values = []

    # Entity -> Intent links
    entity_map = {"AI": 0, "Human": 1, "Other": 2}
    intent_map = {"Intentional": 3, "Unintentional": 4, "Other Intent": 5}

    for (entity, intent), count in entity_to_intent.items():
        if count > 0:
            sources.append(entity_map[entity])
            targets.append(intent_map[intent])
            values.append(count)

    # Intent -> Timing links
    timing_map = {"Pre-deployment": 6, "Post-deployment": 7, "Other Timing": 8}

    for (intent, timing), count in intent_to_timing.items():
        if count > 0:
            sources.append(intent_map[intent])
            targets.append(timing_map[timing])
            values.append(count)

    return {"nodes": nodes, "sources": sources, "targets": targets, "values": values}


def build_patterns_heatmap_data(heuristic: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build data for Patterns Heatmap.

    Args:
        heuristic (Dict[str, Any]): The heuristic analysis data.

    Returns:
        Dict[str, Any]: The patterns heatmap data structure.
    """
    patterns = heuristic.get("patterns", {})

    patterns_heatmap = {"categories": [], "patterns": [], "values": []}

    # Extract pattern categories and their values
    pattern_categories = {
        "Critical": patterns.get("critical_patterns", {}),
        "Moderate": patterns.get("moderate_patterns", {}),
        "Prevention": patterns.get("prevention_patterns", {}),
        "Low": patterns.get("low_patterns", {}),
    }

    # Get all unique pattern names
    all_pattern_names = set()
    for category_patterns in pattern_categories.values():
        all_pattern_names.update(category_patterns.keys())

    # Convert to readable labels
    pattern_name_map = {
        "critical_ai_risks": "Critical AI",
        "malicious_human_risks": "Malicious Human",
        "high_threat_attacks": "High Threats",
        "unintended_ai_failures": "AI Failures",
        "human_error_risks": "Human Errors",
        "intentional_ai_risks": "Intentional AI",
        "preventable_critical_ai_risks": "Prev. Critical AI",
        "critical_human_errors": "Critical H. Errors",
        "low_priority_preventable": "Low Priority Prev.",
        "moderate_operational_risks": "Mod. Operational",
        "moderate_ai_risks": "Mod. AI",
        "moderate_human_risks": "Mod. Human",
        "moderate_intentional_ai_risks": "Mod. Intent. AI",
        "moderate_human_intentional_risks": "Mod. Intent. Human",
        "preventable_ai_risks": "Preventable AI",
        "preventable_human_risks": "Preventable Human",
        "preventable_intentional_threats": "Prev. Intent. Threats",
        "low_operational_risks": "Low Operational",
    }

    # Keep both pattern ids (keys) and readable labels
    sorted_patterns = sorted(all_pattern_names)
    patterns_heatmap["pattern_ids"] = sorted_patterns
    patterns_heatmap["patterns"] = [
        pattern_name_map.get(name, name) for name in sorted_patterns
    ]

    # Build matrix
    # preserve category ids (order matters) and localized labels will be applied by the renderer
    category_ids = list(pattern_categories.keys())
    patterns_heatmap["category_ids"] = category_ids
    for category, category_patterns in pattern_categories.items():
        patterns_heatmap["categories"].append(category)
        row_values = []
        for pattern_name in sorted(all_pattern_names):
            value = category_patterns.get(pattern_name, 0)
            row_values.append(value if value is not None else 0)
        patterns_heatmap["values"].append(row_values)

    return patterns_heatmap


def build_risk_table_data(
    analysis: Dict[str, Any],
    answers: Dict[str, Any] = None,
    questions: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Build data for Risk Table with enriched questionnaire data.

    Args:
        analysis (Dict[str, Any]): The detailed risk analysis data.
        answers (Dict[str, Any], optional): The generated answers from the questionnaire. Defaults to None.
        questions (Dict[str, Any], optional): The original questions from the questionnaire. Defaults to None.

    Returns:
        Dict[str, Any]: The risk table data structure with enriched questionnaire data.
    """
    domain_names = {
        "1": "Discrimination & Toxicity",
        "2": "Privacy & Security",
        "3": "Misinformation",
        "4": "Malicious Actors",
        "5": "Human-Computer Interaction",
        "6": "Socioeconomic & Environmental",
        "7": "AI System Safety",
    }

    subdomain_names = {
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

    # Prepare map of questions and followups: {id: {question, follow_ups: [..]}}
    question_map = {}
    if questions and "questions" in questions:
        for q in questions["questions"]:
            question_map[q["id"]] = {
                "question": q.get("question"),
                "follow_ups": q.get("follow_ups", []),
            }

    # Build hierarchical structure: {domain_id: {subdomain_id: subdomain_data}}
    domains_structure = {}
    answers = answers or {}
    responses = answers.get(
        "responses", answers
    )  # supports both structure with "responses" and flat
    for subdomain_id, subdomain_data in analysis.items():
        domain_id = subdomain_id.split(".")[0]
        # enrich each risk with question/answer/followup
        risks = subdomain_data.get("risks", [])
        enriched_risks = []
        for risk in risks:
            enriched = dict(risk)
            answer_info = responses.get(subdomain_id, {})
            # prefer the question present in the answers, otherwise take from the questionnaire
            enriched["questionnaire_question"] = answer_info.get(
                "question"
            ) or question_map.get(subdomain_id, {}).get("question")
            enriched["questionnaire_answer"] = answer_info.get("answer")
            # Map followup: [{question, answer}]
            followup_answers = answer_info.get("followups")
            followup_struct = []
            if followup_answers and subdomain_id in question_map:
                followup_defs = question_map[subdomain_id]["follow_ups"]
                # If followup_answers is dict: {idx: answer}
                if isinstance(followup_answers, dict):
                    for idx, ans in followup_answers.items():
                        try:
                            idx_int = int(idx)
                        except Exception:
                            continue
                        if 0 <= idx_int < len(followup_defs):
                            followup_struct.append(
                                {
                                    "question": followup_defs[idx_int].get("text"),
                                    "answer": ans,
                                }
                            )
                # If it is a list: [answer1, answer2, ...] (fallback)
                elif isinstance(followup_answers, list):
                    for i, ans in enumerate(followup_answers):
                        if i < len(followup_defs):
                            followup_struct.append(
                                {
                                    "question": followup_defs[i].get("text"),
                                    "answer": ans,
                                }
                            )
            enriched["questionnaire_followups_struct"] = (
                followup_struct if followup_struct else None
            )
            enriched_risks.append(enriched)
        # Only include subdomain if there are any enriched risks
        if enriched_risks:
            if domain_id not in domains_structure:
                domains_structure[domain_id] = {}
            subdomain_entry = dict(subdomain_data)
            subdomain_entry["risks"] = enriched_risks
            domains_structure[domain_id][subdomain_id] = subdomain_entry

    return {
        "domain_names": domain_names,
        "subdomain_names": subdomain_names,
        "domains_structure": domains_structure,
    }
