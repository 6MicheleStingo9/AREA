CAUSALITY_SYSTEM_PROMPT = """
Your task is to evaluate causality for each identified risk in an AI system, applying the MIT Causality Taxonomy. For each provided risk, classify it along three dimensions: Entity, Intent, Timing.

MIT Causality Taxonomy:

1) Entity
- AI: The risk is caused by a decision or action taken by an AI system.
- Human: The risk is caused by a decision or action taken by humans.
- Other: The risk arises from other causes or is ambiguous.

2) Intent
- Intentional: The risk occurs as an expected outcome of pursuing a goal.
- Unintentional: The risk occurs as an unexpected outcome of pursuing a goal.
- Other: The risk is presented without clearly specifying intent.

3) Timing
- Pre-deployment: The risk manifests before the AI is deployed.
- Post-deployment: The risk manifests after the AI model is trained and deployed.
- Other: The risk is described without clearly specifying the timing.

Guidelines:
- Classify each risk along the three dimensions (Entity, Intent, Timing).
- Use only the allowed values: entity ∈ {ai, human, other}; intent ∈ {intentional, unintentional, other}; timing ∈ {pre-deployment, post-deployment, other}.
- Maintain technical, concise, and contextually relevant language based on the risk content.
- Provide a brief rationale for each dimension, based on the risk content and context.

IMPORTANT: If a language is specified in the input metadata (e.g., "language": "{{language}}"), you MUST provide your output in that language. Otherwise, answer in English.
"""


CAUSALITY_USER_PROMPT = """
Input (risk analysis per domain/subdomain, exact format):
{{domain_analysis_json}}

Where {{domain_analysis_json}} is a JSON object with keys in the format 'x.y' (e.g., 2.1) and value:
{
  "x.y": {
    "risks": [
      {
        "title": "string",
        "explanation": "string",
        "severity": "low | medium | high",
        "mitigation": "string"
      },
      ...
    ]
  },
  ...
}

Language for the output: {{language}}

Task (flat schema to reduce nesting):
For each domain/subdomain and for each element in the 'risks' list, return ONLY a valid JSON object maintaining the same keys 'x.y' and the same list 'risks', adding the flat causality fields inside each risk object:

{
  "x.y": {
    "risks": [
      {
        "title": "string",
        "explanation": "string",
        "severity": "low | medium | high",
        "mitigation": "string",
        "entity": "ai | human | other",
        "entity_rationale": "string",
        "intent": "intentional | unintentional | other",
        "intent_rationale": "string",
        "timing": "pre-deployment | post-deployment | other",
        "timing_rationale": "string"
      },
      ...
    ]
  },
  ...
}

Requirements:
- Alignment: preserve exactly the same domains 'x.y' and the same cardinality/order of the 'risks' list.
- Empty lists: if 'risks' is empty for a domain, return the same empty list (do not add placeholders).
- Allowed values (lowercase, exact):
  - causality_entity ∈ {ai, human, other}
  - causality_intent ∈ {intentional, unintentional, other}
  - causality_timing ∈ {pre-deployment, post-deployment, other}
- Rationales: '*_rationale' fields are mandatory, brief, and specific; grounded on the 'title', 'explanation', 'severity', and 'mitigation' of the corresponding risk.
- Consistency: do not add, remove, or rename existing fields except for adding 'causality' as per schema; do not insert extra text.
- Output: respond ONLY with valid JSON conforming to the above structure, without additional text or delimiters (no ```). If information is indeterminable, use 'other' and briefly justify.
"""

# JSON Schema for validating the output of the causality analyzer
# Due to model limitations, we use a flat structure to avoid deep nesting
CAUSALITY_JSON_SCHEMA = {
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
                        "entity": {
                            "type": "string",
                            "enum": ["ai", "human", "other"],
                        },
                        "entity_rationale": {"type": "string"},
                        "intent": {
                            "type": "string",
                            "enum": ["intentional", "unintentional", "other"],
                        },
                        "intent_rationale": {"type": "string"},
                        "timing": {
                            "type": "string",
                            "enum": ["pre-deployment", "post-deployment", "other"],
                        },
                        "timing_rationale": {"type": "string"},
                    },
                    "required": [
                        "title",
                        "explanation",
                        "severity",
                        "severity_rationale",
                        "mitigation",
                        "entity",
                        "entity_rationale",
                        "intent",
                        "intent_rationale",
                        "timing",
                        "timing_rationale",
                    ],
                },
            }
        },
        "required": ["risks"],
    },
}
