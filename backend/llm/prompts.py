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