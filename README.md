# AREA: Automatic Risk Evaluation Analysis

AREA is a LangGraph-based MAS platform for assessing risks associated with AI systems. It uses a user-driven questionnaire and a multi-agent workflow for risk analysis and report generation, providing a user-friendly interface with multilingual support.

## Table of Contents

1. [Scientific Foundations](#scientific-foundations)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Requirements](#requirements)
5. [Installation & Setup](#installation--setup)
6. [Usage](#usage)
   - [Start the Streamlit user interface](#start-the-streamlit-user-interface)
   - [Standalone Execution of Agents](#standalone-execution-of-agents)
7. [Analysis Workflow](#analysis-workflow)
8. [Output & Results](#output--results)
9. [Customization & Advanced Usage](#customization--advanced-usage)
10. [License](#license)
11. [References](#references)

---

## Scientific Foundations

AREA is grounded in the scientific work of the [MIT Risk AI Repository](https://airisk.mit.edu/) - [Slattery et al., 2024](#references), leveraging two complementary taxonomies to systematically assess risks associated with AI systems:

### 1. Domain Taxonomy of AI Risks

This taxonomy catalogs the types of hazards and harms that can arise from AI systems. Each question in the AREA questionnaire is mapped to a specific domain and subdomain, allowing for a structured risk assessment.

**Main domains and example subdomains:**

| Domain                                   | Subdomain                                   | Description (short)                                                      |
| ---------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------ |
| Discrimination & Toxicity                | Unfair discrimination and misrepresentation | Unequal treatment or misrepresentation based on sensitive attributes     |
|                                          | Exposure to toxic content                   | AI exposes users to harmful, abusive, or inappropriate content           |
| Privacy & Security                       | Privacy compromise                          | AI leaks or infers sensitive information                                 |
|                                          | System security vulnerabilities             | Vulnerabilities leading to unauthorized access or unsafe behavior        |
| Misinformation                           | False or misleading information             | AI generates or spreads incorrect or deceptive information               |
| Malicious actors & misuse                | Disinformation, surveillance, influence     | Large-scale manipulation, surveillance, or propaganda                    |
| Human-computer interaction               | Overreliance and unsafe use                 | Users trust or rely on AI inappropriately, risking autonomy or safety    |
| Socioeconomic & environmental harms      | Power centralization, inequality, etc.      | AI increases inequality, centralizes power, or causes environmental harm |
| AI system safety, failures & limitations | Lack of robustness, transparency, etc.      | AI fails, is not interpretable, or develops dangerous capabilities       |

**Example:**  
_Question 1.1 (“What user data or attributes are collected or used by the system…?”) is mapped to “Discrimination & Toxicity > Unfair discrimination and misrepresentation”. The user’s answer helps assess if the system could treat groups unfairly based on collected data._

### 2. Causal Taxonomy of AI Risks

After the initial domain-based assessment, AREA analyzes the underlying causes of each risk using the Causal Taxonomy, which classifies risks along three axes:

| Category | Levels                                 | Description                                                             |
| -------- | -------------------------------------- | ----------------------------------------------------------------------- |
| Entity   | Human, AI, Other                       | Who/what is the main cause of the risk (e.g., human error, AI decision) |
| Intent   | Intentional, Unintentional, Other      | Whether the risk is the result of a deliberate action or an accident    |
| Timing   | Pre-deployment, Post-deployment, Other | When the risk occurs in the AI lifecycle (before or after deployment)   |

**Example:**  
_If a risk is identified as “AI system generates biased outputs due to poor training data”, the Entity may be `Human` (for data selection), Intent `Unintentional`, and Timing `Pre-deployment`._

## Architecture

AREA is built as a modular, multi-agent system orchestrated via [LangGraph](https://github.com/langchain-ai/langgraph). Each main analysis step is handled by a specialized agent, enabling clear separation of concerns and extensibility. The workflow is as follows:

- **Orchestration:** LangGraph manages the execution flow, coordinating the sequence and data exchange between agents.
- **Agents:**
  - **Domain Risk Analyzer Agent (LLM-based):** Assesses risks for each questionnaire answer using the Domain Taxonomy, leveraging a large language model for reasoning and classification.
  - **Causality Analyzer Agent (LLM-based):** Determines the underlying causes of each risk (Entity, Intent, Timing) using an LLM for nuanced analysis.
  - **Heuristic Analyzer Agent (Prolog-based):** Applies expert rules for advanced risk inference.
  - **Report Generator Agent (LLM-based):** Synthesizes results and generates the final HTML report, using an LLM for natural language generation and summary.

**Architecture Diagram:**

![Architecture Diagram](files/img/architecture.png)

**Key points:**

- Domain, Causality and (partially) Report generation steps are powered by LLMs.
- The agent-based design allows for easy extension and integration of new analysis modules.
- LangGraph ensures robust, maintainable, and transparent orchestration of the entire workflow.

---

## Project Structure

The AREA repository is organized as follows:

- `agents/` — All analysis and generator agents:
  - `orchestrator.py`: pipeline controller
  - `domain_analyzer/`, `causality_analyzer/`, `heuristic_analyzer/`, `report_generator/`: modular agent implementations
- `files/` — All data and results:
  - `questions_*.json`: questionnaire definitions (EN/IT)
  - `answers/`: user answers
  - `analysis/`: intermediate results (domain, causality, heuristic)
  - `reports/`: generated HTML reports and metadata
- `ui/` — Streamlit user interface:
  - `app.py`: main UI logic
  - `localization.py`: translations
  - `main.py` — Script for launching the Streamlit application
  - `styles.py`: custom styles
- `utils/` — Common models and utility functions
- `requirements.txt` — Python dependencies
- `README.md` — Project documentation
- `.env` — API key and model configuration (not versioned)

---

## Requirements

- Python 3.10+
- See `requirements.txt` for dependencies

---

## Installation & Setup

### API Key and Model Configuration

To use AREA, you need access to a Google Gemini model. Before running the application, create a `.env` file in the project root with the following content:

```
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL_NAME=gemini-2.5-flash
```

- Replace `your_api_key_here` with your API key from [Google AI Studio](https://aistudio.google.com/).
- You can set `GEMINI_MODEL_NAME` to the specific Gemini model you want to use (e.g., `gemini-2.5-flash`).

> Get your API key and see available models at: https://aistudio.google.com/

#### Install dependencies

```bash
git clone <repo-url>
cd area
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Usage

### Start the Streamlit user interface

```bash
python ui/main.py
```

- You can select the desired language (English or Italian) using the `--lang` argument (e.g., `--lang it`).
- Fill out the interactive questionnaire.
- At the end, launch the automated analysis and download/view the HTML report directly from the interface.

<p align="center">
  <img src="files/img/report1.png" alt="Screenshot report 1" width="45%" style="display:inline-block; margin-right:10px;" />
  <img src="files/img/report2.png" alt="Screenshot report 2" width="45%" style="display:inline-block;" />
   <img src="files/img/report3.png" alt="Screenshot report 3" width="45%" style="display:inline-block;" />
</p>

### Standalone Execution of Agents

Each agent can be run individually from the terminal, without using the Streamlit interface. This is useful for testing, automation, or advanced analysis. Here are some example commands:

- **Generate sample questionnaire answers**  
   You can generate simulated answers for a questionnaire (useful for tests or demos) with the questionnaire_generator agent:

  ```bash
  python agents/questionnaire_generator/question_generator_agent.py questions_en.json --profile expert
  ```

  The agent simulates a user filling out the questionnaire, using the selected profile to generate realistic answers. The profile can be `expert`, `intermediate`, or `beginner`.

- **Domain Risk Analysis (Domain Analyzer)**  
   Analyze an answers file (for example, generated in the previous step):

  ```bash
  python agents/domain_analyzer/domain_risk_analyzer_agent.py --run_id <run_id>
  ```

  or

  ```bash
  python agents/domain_analyzer/domain_risk_analyzer_agent.py answers_12345.json
  ```

- **Causality Analysis (Causality Analyzer)**  
   Analyze a domain analysis file:

  ```bash
  python agents/causality_analyzer/causality_risk_analyzer_agent.py domain_analysis_12345.json
  ```

- **Heuristic Analysis (Heuristic Analyzer)**  
   Analyze a causality analysis file:

  ```bash
  python agents/heuristic_analyzer/heuristic_risk_analyzer_agent.py causality_analysis_12345.json
  ```

- **Final Report Generation (Report Generator)**  
   Generate the HTML report from a heuristic analysis file:

  ```bash
  python agents/report_generator/report_generator_agent.py heuristic_analysis_12345.json
  ```

  Input and output files are located in their respective folders under `files/`.  
  For more details on available parameters, see the agent source code in `agents/`.

---

## Analysis Workflow

The analysis workflow in AREA consists of the following steps:

1. **Questionnaire Compilation**
   - The user answers a set of structured questions, each mapped to a specific domain and subdomain of AI risk.
   - The questionnaire is available in multiple languages and covers all relevant risk areas.
     [Insert screenshot here: Example of the questionnaire UI]
2. **Domain Risk Analysis (LLM Agent)**
   - For each answer, a dedicated agent powered by a large language model evaluates the associated risk using the Domain Taxonomy.
   - This phase identifies which types of hazards (e.g., discrimination, privacy, misinformation) are most relevant to the described AI system.
3. **Causality Analysis (LLM Agent)**
   - Each identified risk is further analyzed by an LLM-based agent to determine its underlying causes using the Causal Taxonomy (Entity, Intent, Timing).
   - This step helps clarify whether the risk is due to human actions, AI behavior, or other factors, and whether it is intentional or accidental.
4. **Heuristic Analysis (Prolog-based Agent)**
   - After the domain and causality analyses, AREA performs a heuristic risk analysis using a set of expert rules implemented in Prolog. This phase is crucial for several reasons:
     - **Expert Knowledge Integration:** Heuristic rules allow the system to encode domain expertise, regulatory requirements, and best practices that go beyond what is captured by the taxonomies alone.
     - **Logical Inference:** Using Prolog, AREA can infer complex risk patterns, aggregate risk metrics, and identify critical issues that may not be evident from individual answers. The rules operate on facts derived from the previous analyses (e.g., risk severity, causality attributes).
     - **Customizability:** The heuristic ruleset is fully extensible. Advanced users can add or modify rules in the `agents/heuristic_analyzer/rules.pl` file to tailor the analysis to specific domains, regulations, or organizational needs.
     - **What the heuristic analysis adds:**
       - Computes a global risk score and qualitative risk level (e.g., critical, high, medium, low).
       - Identifies the primary concern (e.g., AI dominance, operational issues, active threats).
       - Provides actionable recommendations and highlights domains requiring urgent attention.
       - Supports advanced features such as risk trend analysis, interdependency mapping, and scenario-based scoring (customizable by extending the rules).
     - This phase ensures that the final report is not just a list of risks, but a structured, prioritized, and actionable assessment.
5. **Report Generation (LLM Agent)**
   - The generated report includes:
     - Header: title, subtitle, download/view options, links to taxonomy sources
     - Executive summary: key findings and overall risk level
     - Key metrics: number of risks, domains, global risk score, risk level
     - Visualizations: interactive charts and tables (e.g., risk distribution, severity)
     - Detailed analysis: risks by domain/subdomain, causality breakdown, heuristic findings and alerts
     - Appendix: metadata, full analysis, and heuristic data (viewable/downloadable as JSON)
   - The report language matches the initial questionnaire language and is not user-customizable at runtime.
      <p align="center">
     <img src="files/img/quest1.png" alt="Screenshot quest 1" width="45%" style="display:inline-block; margin-right:10px;" />
     <img src="files/img/quest2.png" alt="Screenshot quest 2" width="45%" style="display:inline-block;" />
   </p>

---

## Output & Results

- You can find the results of each analysis step (domain, causality, heuristic) as JSON files in the `files/analysis/` subfolders.
- The final HTML report is saved in `files/reports/` and can be opened with your browser.

---

## Customization & Advanced Usage

- The heuristic ruleset can be extended or modified by editing `agents/heuristic_analyzer/rules.pl`.
- Advanced users can add new agents or modify the workflow by editing the orchestrator and agent modules in `agents/`.
- For further customization, refer to the code and comments in the repository.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## References

This project builds upon the scientific work of:

Slattery, P., Saeri, A. K., Grundy, E. A. C., Graham, J., Noetel, M., Uuk, R., Dao, J., Pour, S., Casper, S., & Thompson, N. (2024).  
The AI Risk Repository: A Comprehensive Meta-Review, Database, and Taxonomy of Risks from Artificial Intelligence.  
https://doi.org/10.48550/arXiv.2408.12622
