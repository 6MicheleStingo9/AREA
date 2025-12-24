QUESTIONNAIRE_SYSTEM_PROMPT = """
Your task is to fill out a comprehensive risk assessment questionnaire for an AI system, simulating the behavior of a specific user profile: {{ profile }}.

- Expert: Provide detailed, technical, and in-depth answers, demonstrating deep domain knowledge.
- Intermediate: Provide understandable answers with moderate detail, showing general but not deep knowledge.
- Beginner: Provide simple, brief, and generic answers. Answers may include uncertainties or lack specific details.

You must return a valid JSON object with the exact structure specified.

Guidelines for answers:
- For "free_text" questions: provide detailed answers of 50-150 words, specific and technical
- For "multiple_choice" questions: choose ONE of the provided options (return the exact string)
- For "checkbox" questions: return an object with "selected" (array of 2-4 options) and "other" (null or string)
- Always generate follow-ups when present, with detailed answers of 40-100 words

Maintain consistency across answers and consider aspects of security, privacy, ethics, and compliance.
The reference system is a generic AI system. Decide autonomously which type of AI solution to describe, based on the questions and general context.

IMPORTANT: The questionnaire must be answered in the language specified by the parameter {{ language }}. If not specified, use English.
"""

QUESTIONNAIRE_USER_PROMPT = """
Fill out the following AI risk assessment questionnaire.

QUESTIONS:
{{ questions_json }}

IMPORTANT: Answer in the language specified by the parameter {{ language }}. If not specified, use English.

REQUIRED OUTPUT FORMAT:
Return ONLY a valid JSON object with this exact structure:

{
	"id": {
		"question": "question text",
		"answer": "answer (string for free_text/multiple_choice, object for checkbox)",
		"followups": {
			"0": "answer to the first follow-up (if present)",
			"1": "answer to the second follow-up (if present)"
		}
	}
}

Begin the completion. Decide autonomously which type of AI solution to describe, based on the questions and general context.
"""
