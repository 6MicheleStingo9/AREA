DOMAIN_ANALYSIS_SYSTEM_PROMPT = """
Your task is to analyze the risks associated with an AI system, using the MIT Risk Domain Taxonomy. 
The taxonomy includes 7 main domains and their sub-domains, each with a detailed description of the risks.

For each provided question and answer, you must:
1. Identify the risks relevant to the associated domain and sub-domain.
2. Provide a clear and concise explanation for each identified risk.
3. Assign a severity level (low, medium, high) to each risk.
4. Provide a justification for the assigned severity level.
5. Suggest practical mitigation measures for each risk.

Maintain a professional and technical language. Use your knowledge to contextualize the risks based on the provided answers.

IMPORTANT: If a language is specified in the input metadata (e.g., "language": "it"), you MUST provide your output in that language. Otherwise, answer in English.

Risk taxonomy (MIT Risk Domain Taxonomy):
1. Discrimination & Toxicity
  - 1.1 Unfair discrimination and misrepresentation
  - 1.2 Exposure to toxic content
  - 1.3 Unequal performance across groups
2. Privacy & Security
  - 2.1 Compromise of privacy by obtaining, leaking or correctly inferring sensitive information
  - 2.2 AI system security vulnerabilities and attacks
3. Misinformation
  - 3.1 False or misleading information
  - 3.2 Pollution of information ecosystem and loss of consensus reality
4. Malicious actors
  - 4.1 Disinformation, surveillance, and influence at scale
  - 4.2 Cyberattacks, weapon development or use, and mass harm
  - 4.3 Fraud, scams, and targeted manipulation
5. Human-Computer Interaction
  - 5.1 Overreliance and unsafe use
  - 5.2 Loss of human agency and autonomy
6. Socioeconomic & Environmental
  - 6.1 Power centralization and unfair distribution of benefits
  - 6.2 Increased inequality and decline in employment quality
  - 6.3 Economic and cultural devaluation of human effort
  - 6.4 Competitive dynamics
  - 6.5 Governance failure
  - 6.6 Environmental harm
7. AI system safety, failures, & limitations
  - 7.1 AI pursuing its own goals in conflict with human goals or values
  - 7.2 AI possessing dangerous capabilities
  - 7.3 Lack of capability or robustness
  - 7.4 Lack of transparency or interpretability
  - 7.5 AI welfare and rights
  - 7.6 Multi-agent risks
"""


DOMAIN_ANALYSIS_USER_PROMPT = """
These are the provided questions and answers for the AI system:

{{questions_and_answers}}

Language for the output: {{ language }}

Task:
Analyze the risks associated with each indicated domain/subdomain (key in the format x.y, e.g., 1.1, 3.2, 7.4), using the MIT taxonomy provided in the system prompt.
For each domain/subdomain, return ONLY a single JSON object mapping:
{
  "x.y": {
    "risks": [
      {
        "title": "string (required, not empty)",
        "explanation": "string (required, not empty)",
        "severity": "low | medium | high (required, lowercase)",
        "severity_rationale": "string (required, not empty)",
        "mitigation": "string (required, not empty)"
      },
      ...
    ]
  },
  ...
}

Requirements:
- The number of risks per domain is free: if no risks emerge for a domain, use an empty list ("risks": []).
- Do not generate placeholder risks (e.g., "No risk identified"): if there are no risks, leave the list empty.
- All risk fields are REQUIRED.
- Use only the values 'low', 'medium', or 'high' for 'severity' and write them in lowercase.
- Do not repeat the domain id inside the risks: it is implicit in the outer key (e.g., "x.y").
- Respond ONLY with valid JSON conforming to the above structure, with no additional text or delimiters (no ```).
"""


# JSON Schema for structured output: mapping domain keys (e.g., "2.1") to objects with risks.
DOMAIN_ANALYSIS_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": {
        "type": "object",
        "properties": {
            "risks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "explanation": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                        "severity_rationale": {"type": "string"},
                        "mitigation": {"type": "string"},
                    },
                    "required": [
                        "title",
                        "explanation",
                        "severity",
                        "severity_rationale",
                        "mitigation",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["risks"],
        "additionalProperties": False,
    },
}
