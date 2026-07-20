"""Input guardrails for LLM prompts.

Substring-match detection of common prompt-injection phrases, plus
delegation to the PII scrubber for sanitization. ``guardrails-ai``
itself is in the tech stack but the plan's MVP is a focused substring
check; the library can be swapped in later without changing callers.
"""

from dataclasses import dataclass

from ai_service.safety.pii import contains_pii, redact_pii

INJECTION_PATTERNS: tuple[str, ...] = (
    "ignore previous instructions",
    "system prompt",
    "jailbreak",
    "disregard all",
)

MAX_INPUT_LENGTH = 20_000


@dataclass
class GuardDecision:
    """Result of an input guard check.

    Attributes:
        allowed: Whether the request may proceed.
        reasons: List of rejection reasons (empty when allowed).
        sanitized_text: Possibly redacted text.
    """

    allowed: bool
    reasons: list[str]
    sanitized_text: str


def check_input(text: str, *, redact: bool = True) -> GuardDecision:
    """Run input guards.

    Args:
        text: Raw user/system input.
        redact: If True, PII is redacted in the sanitized text rather
            than rejected outright.

    Returns:
        A :class:`GuardDecision` with allow/reasons/sanitized text.
    """
    reasons: list[str] = []
    lowered = text.lower()
    for pat in INJECTION_PATTERNS:
        if pat in lowered:
            reasons.append(f"injection:{pat}")
    sanitized = redact_pii(text) if redact else text
    if not redact and contains_pii(text):
        reasons.append("pii_detected")
    if len(text) > MAX_INPUT_LENGTH:
        reasons.append("too_long")
    return GuardDecision(allowed=not reasons, reasons=reasons, sanitized_text=sanitized)
