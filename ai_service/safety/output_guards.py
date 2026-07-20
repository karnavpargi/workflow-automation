"""Output guardrails for LLM responses.

The MVP always scrubs PII from model output. Future work can add
schema validation, toxicity checks, or other guardrails-ai validators.
"""

from ai_service.safety.pii import redact_pii


def check_output(text: str) -> str:
    """Scrub PII from a model output.

    Args:
        text: Raw model output.

    Returns:
        Cleaned text.
    """
    return redact_pii(text)
