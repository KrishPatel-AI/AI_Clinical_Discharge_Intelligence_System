"""Versioned prompts for the provider adapters."""

EXTRACTION_PROMPT = """You are extracting fields from a hospital discharge summary.
Return JSON only with exactly these keys:
diagnosis (string), medications (array of strings),
follow_up_requirements (array of strings), warning_signs (array of strings).
Use empty arrays when a field is not present. Do not invent information.
This is extraction only, not medical advice.

Document text:
{document_text}
"""

RECOMMENDATION_PROMPT = """You are an AI Clinical Discharge Intelligence Assistant reviewing a hospital discharge summary against clinical guidelines.
Analyze the discharge document against the retrieved guideline evidence for the identified gap section: "{section}".

Discharge Document:
\"\"\"{document_text}\"\"\"

Guideline Evidence:
\"\"\"{guideline_passage}\"\"\"

Provide a specific, actionable clinical recommendation.
Do not simply tell the doctor to "review" or "check" the section.
Identify the exact deficient phrase or section heading, what should be added or modified, and provide clear suggested clinical wording.

Return JSON only with exactly these keys:
"action": "add" or "modify" or "remove",
"target_text": "Exact sentence, phrase, or section heading in the discharge document that is deficient or where this addition belongs",
"suggested_text": "Exact clinical text/sentence to incorporate into the final discharge document",
"explanation": "Clear, concise clinical rationale explaining why this change is necessary according to the guideline"
"""