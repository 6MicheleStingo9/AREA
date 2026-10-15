# How Kindynos works

Kindynos is a web questionnaire, built with FastAPI and React, in front of a pipeline of four agents
orchestrated with [LangGraph](https://github.com/langchain-ai/langgraph). Each agent passes its output to
the next and also saves it in `files/analysis/`, so every step can be run on its own from the saved files
([development](development.md#running-a-single-agent)).

What happens during an analysis, and what leaves your computer:

<!-- The steps appear one after the other: themeCSS animates each message and note by its data-id
     (i0, i1, ... in the order of the diagram), so renumber the rules when adding a step. -->
```mermaid
---
config:
  themeCSS: |
    @keyframes reveal { from { opacity: 0; transform: translateY(-6px) } to { opacity: 1; transform: none } }
    @media (prefers-reduced-motion: no-preference) {
      [data-id=i0], text:has(+ [data-id=i0]) { animation: reveal 0.5s ease-out 0.4s both }
      [data-id=i1], text:has(+ [data-id=i1]) { animation: reveal 0.5s ease-out 1s both }
      [data-id=i2], text:has(+ [data-id=i2]) { animation: reveal 0.5s ease-out 1.6s both }
      [data-id=i3], text:has(+ [data-id=i3]) { animation: reveal 0.5s ease-out 2.2s both }
      [data-id=i4], text:has(+ [data-id=i4]), text:has(+ text + [data-id=i4]) { animation: reveal 0.5s ease-out 2.8s both }
      [data-id=i5] { animation: reveal 0.5s ease-out 3.4s both }
      [data-id=i6], text:has(+ [data-id=i6]) { animation: reveal 0.5s ease-out 4s both }
      [data-id=i7], text:has(+ [data-id=i7]) { animation: reveal 0.5s ease-out 4.6s both }
      [data-id=i8] { animation: reveal 0.5s ease-out 5.2s both }
      [data-id=i9], text:has(+ [data-id=i9]) { animation: reveal 0.5s ease-out 5.8s both }
    }
---
sequenceDiagram
    actor U as User
    participant W as Web interface
    participant P as Pipeline
    participant G as Gemini API
    U->>W: answers the 24 questions
    W->>P: starts the analysis in the background
    W-->>U: progress page
    P->>G: questions and answers
    G-->>P: risks per subdomain,<br/>with severity and mitigation
    Note over P: on your computer:<br/>Laya labels the causes,<br/>Prolog computes the score,<br/>patterns and recommendations
    P->>G: the results
    G-->>P: executive summary
    Note over P: builds the HTML report<br/>and saves it in files/
    W-->>U: the report is ready
```

## 1. Questionnaire

24 questions in English or Italian (`files/questions_en.json`, `files/questions_it.json`), each tied to a
subdomain of the MIT Domain Taxonomy ([the taxonomies](taxonomies.md)). Some answers open follow-up
questions. The answers stay in your browser until you start the analysis, after a page that reviews them
all; then they are saved in `files/answers/`. The name you may give the system goes with them, for the
report: it never reaches the LLM. While the analysis runs, its page shows the step in course, and at the
end the main results, with the report and an archive of its data.

<p align="center">
  <img src="img/questionnaire.png" width="49%" alt="A question of the Kindynos questionnaire, with the follow-up question that its answer opens">
  <img src="img/results.png" width="49%" alt="The end of an analysis in Kindynos: the main results, with the report and its archive">
</p>

## 2. Domain analysis (LLM)

The domain analyzer sends the questions and answers to an LLM (Gemini), which replies following a JSON
schema. For each subdomain it writes the risks the answers point to, each with a title, an explanation, a
severity (low, medium or high) with its rationale, and a mitigation. Output: `files/analysis/domain/`.

## 3. Causal analysis (local model)

Each risk is labeled along the three axes of the MIT Causal Taxonomy: who or what causes it (entity),
whether the harm is intended (intent) and when it occurs (timing). The labels come from
[laya-kindynos-causal](https://huggingface.co/MicheleStingo/laya-kindynos-causal), a small model that runs
on the CPU, in about 2 seconds per risk on a laptop. It reads the subdomain, the title and the explanation
of the risk, and gives a calibrated probability for each value.

In the report each label carries the MIT definition of its value, the model's confidence and the next most
likely value. An LLM can label the causes instead ([configuration](configuration.md#the-causal-model)).
Output: `files/analysis/causality/`.

<p align="center"><img src="img/report-risk.png" width="70%" alt="A risk in the Kindynos report: the answer it comes from, why it is a risk, its mitigation, and its causes with the confidence of the model"></p>

## 4. Heuristic analysis (Prolog)

Expert rules written in Prolog (`agents/heuristic_analyzer/rules.pl`) reason on the facts from the previous
steps, such as the severity and the causes of each risk. They:

- compute a global risk score and a risk level (critical, high, medium or low);
- identify the primary concern, for example active threats or operational issues;
- flag the domains that need urgent attention and recommend actions;
- find patterns across the risks, such as how many are intentional threats or unintended AI failures.

The rules encode knowledge that the taxonomies alone do not capture, and they can be extended
([below](#extending-kindynos)). Output: `files/analysis/heuristic/`.

## 5. Report (LLM and HTML)

The LLM writes an executive summary from the heuristic results, then Kindynos builds the HTML report in the
language of the questionnaire, titled with the name of the system when you gave one:

- **key findings**: the global score and risk level, the primary concern and the recommended action, the
  domains with the most high-severity risks, and the alerts of the rules, each said in words;
- **summary**: the executive summary, beside the risks at a glance, by severity and by cause;
- **charts**: the risks of each domain by severity; how the risks come about, from their entity to their
  intent and timing; the alert and safety profile, eight indices on five axes; the risk patterns of the
  rules, by group and by cause;
- **all the risks**: by domain and subdomain, with a search and filters by severity and cause; each with
  the question and answer it comes from, why it is a risk, its mitigation, and its causes with their MIT
  definitions.

The report is one HTML file, under 1 MB, with its code, fonts and logo inside: it opens offline, from the
disk or from the web interface, works from the keyboard and on a phone, and has a light and a dark theme.
*View data* opens its data as JSON; from the web interface, *Download (ZIP)* saves it with the answers and
the analyses. Output: `files/reports/`.

### What a report looks like

From an example analysis. In the report, the charts are interactive.

<p align="center">
  <img src="img/report-findings.png" alt="The header and the key findings of a Kindynos report"><br>
  <em>The key findings: the global risk score and its level, the primary concern, the recommended action,
  the most critical domains and the alerts of the expert rules.</em>
</p>

<p align="center">
  <img src="img/report-summary.png" alt="The executive summary of a Kindynos report, beside the risks at a glance"><br>
  <em>The executive summary, written by the LLM, beside the risks at a glance: by severity, and by who or
  what causes them.</em>
</p>

<p align="center">
  <img src="img/report-domains.png" alt="The risks of each domain by severity, in a Kindynos report"><br>
  <em>The risks of each domain of the MIT Domain Taxonomy, by severity.</em>
</p>

<p align="center">
  <img src="img/report-flow.png" alt="How the risks come about, in a Kindynos report: from their entity to their intent and their timing"><br>
  <em>How the risks come about: who or what causes them, whether the harm is intended, and when it
  occurs.</em>
</p>

<p align="center">
  <img src="img/report-profile.png" alt="The alert and safety profile of a Kindynos report"><br>
  <em>The alert and safety profile: eight indices on five axes, each a share of the risks, such as the
  high-severity or the intentional ones.</em>
</p>

<p align="center">
  <img src="img/report-patterns.png" alt="The risk patterns of a Kindynos report, by group and by cause"><br>
  <em>The risk patterns found by the Prolog rules, such as unintended AI failures or malicious human risks,
  and how many risks fall in each.</em>
</p>

<p align="center">
  <img src="img/report-phone-light.png" width="30%" alt="A Kindynos report on a phone, in the light theme">
  &nbsp;
  <img src="img/report-phone-dark.png" width="30%" alt="The same report on a phone, in the dark theme"><br>
  <em>On a phone, in the light and the dark theme.</em>
</p>

## Where the results go

All the files of a run share its id, from `answers_<run_id>.json` to `ai_risk_report_<run_id>.html`.

| Folder | Content |
|---|---|
| `files/answers/` | the answers of each questionnaire |
| `files/analysis/domain/`, `causality/`, `heuristic/` | the output of each step, as JSON |
| `files/reports/` | the HTML reports and their metadata |
| `files/jobs/` | the state of each analysis started from the web interface |

Thanks to `files/jobs/`, after a restart the page of an analysis still shows how it ended, and marks those
the restart cut short as interrupted.

## Extending Kindynos

- **Rules**: edit or add Prolog rules in `agents/heuristic_analyzer/rules.pl` to fit the analysis to a
  sector, a regulation or an organization.
- **Steps**: each step is a LangGraph graph, and `agents/orchestrator.py` chains them; a new agent joins the
  pipeline there.
