"""
HTML Report Generator
Creates interactive dashboard using Jinja2 templates with Plotly visualizations
"""

import json
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader

from .chart_data_builder import prepare_chart_data, build_risk_table_data


REPORT_DIR = Path(__file__).parent.parent.parent / "files" / "reports"
TEMPLATE_DIR = Path(__file__).parent / "templates"
STYLES_DIR = Path(__file__).parent / "styles"
SCRIPTS_DIR = Path(__file__).parent / "scripts"


def load_css() -> str:
    """
    Load and concatenate all CSS files.

    Returns:
        str: The combined CSS content.
    """
    css_files = ["base.css", "components.css", "charts.css"]
    css_content = []
    for css_file in css_files:
        css_path = STYLES_DIR / css_file
        if css_path.exists():
            css_content.append(css_path.read_text(encoding="utf-8"))
    return "\n".join(css_content)


def load_js() -> str:
    """
    Load and concatenate all JavaScript files.

    Returns:
        str: The combined JavaScript content.
    """
    js_files = ["charts.js", "navigation.js", "filters.js"]
    js_content = []
    for js_file in js_files:
        js_path = SCRIPTS_DIR / js_file
        if js_path.exists():
            js_content.append(js_path.read_text(encoding="utf-8"))
    return "\n".join(js_content)


def load_translations(language: str) -> dict:
    """
    Load translations from JSON file based on the selected language.

    Args:
        language (str): The language code.

    Returns:
        dict: A dictionary of translations.
    """
    translations_path = (
        Path(__file__).parent.parent.parent
        / "agents"
        / "report_generator"
        / "templates"
        / "translations.json"
    )
    if translations_path.exists():
        with open(translations_path, "r", encoding="utf-8") as f:
            translations = json.load(f)
        return translations.get(language, {})
    return {}


def generate_html_report(
    metadata: Dict[str, Any],
    heuristic: Dict[str, Any],
    analysis: Dict[str, Any],
    questionnaire: Dict[str, Any] = None,
) -> Path:
    """
    Generate interactive HTML report with Plotly visualizations.

    Args:
        metadata (Dict[str, Any]): Metadata about the analysis run.
        heuristic (Dict[str, Any]): Heuristic data used in the analysis.
        analysis (Dict[str, Any]): The analysis results data.
        questionnaire (Dict[str, Any], optional): User questionnaire answers. Defaults to None.

    Returns:
        Path: The path to the generated HTML report.
    """
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    run_id = metadata.get("run_id")
    if not run_id:
        raise RuntimeError(
            "Missing run_id in metadata; report generation requires run_id produced by domain analyzer"
        )
    filename = f"ai_risk_report_{run_id}.html"
    html_path = REPORT_DIR / filename

    # Load template using Jinja2 Environment
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("report_template.html")

    # Prepare chart data
    chart_data = prepare_chart_data(heuristic, analysis)

    # Prefer `questionnaire` parameter when the caller provided answers (state passes it).
    # Fallback to metadata 'answers' if questionnaire is not provided.
    answers = questionnaire or {}

    # Load questions dynamically based on language
    language = metadata.get("language", "en")
    translations = load_translations(language)
    questions_path = (
        Path(__file__).parent.parent.parent / "files" / f"questions_{language}.json"
    )
    questions = {}
    if questions_path.exists():
        with open(questions_path, "r", encoding="utf-8") as f:
            questions = json.load(f)

    risk_table_data = build_risk_table_data(analysis, answers, questions)

    # Localize patterns heatmap labels (server-side): map pattern ids and category ids
    try:
        ph = chart_data.get("patterns_heatmap", {})
        # Patterns
        pattern_ids = ph.get("pattern_ids") or []
        pattern_labels = ph.get("patterns") or []
        if pattern_ids:
            localized_patterns = [
                translations.get(
                    "pattern_" + pid,
                    pattern_labels[i] if i < len(pattern_labels) else pid,
                )
                for i, pid in enumerate(pattern_ids)
            ]
            ph["patterns"] = localized_patterns

        # Categories
        category_ids = ph.get("category_ids") or []
        category_labels = ph.get("categories") or []
        if category_ids:
            localized_cats = [
                translations.get(
                    "pattern_category_" + cid.lower(),
                    category_labels[i] if i < len(category_labels) else cid,
                )
                for i, cid in enumerate(category_ids)
            ]
            ph["categories"] = localized_cats
    except Exception:
        pass

    # Render template with inline CSS and JS
    html_content = template.render(
        metadata=metadata,
        heuristic=heuristic,
        analysis=analysis,
        translations=translations,
        chart_data=chart_data,
        domain_names=risk_table_data["domain_names"],
        subdomain_names=risk_table_data["subdomain_names"],
        domains_structure=risk_table_data["domains_structure"],
        css_content=load_css(),
        js_content=load_js(),
        language=language,  # Pass language to the template
    )

    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    except Exception as e:
        # Log or handle the error as needed
        raise RuntimeError(f"HTML report generation failed: {str(e)}")
    return html_path
