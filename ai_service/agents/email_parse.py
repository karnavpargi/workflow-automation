"""LangGraph agent: parse an email and extract structured fields.

Two-node graph: ``guard`` (input checks + PII redaction) -> ``extract``
(structured LLM call). If the guard rejects, the extractor returns a
sentinel ``{category: "unknown"}`` result and the LLM is never invoked.
"""

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from ai_service.llm.factory import get_chat_model
from ai_service.safety.input_guards import check_input
from ai_service.safety.output_guards import check_output


class EmailFields(BaseModel):
    """Structured fields extracted from an email.

    Attributes:
        category: ``contact`` | ``invoice`` | ``support`` | ``unknown``.
        name: Sender name if present.
        email: Sender email if present.
        amount: Invoice amount if mentioned.
        summary: One-line summary.
    """

    category: str = Field(
        default="unknown", description="contact|invoice|support|unknown"
    )
    name: str = ""
    email: str = ""
    amount: str = ""
    summary: str = ""


class EmailState(TypedDict, total=False):
    """Graph state for email parsing."""

    raw: str
    sanitized: str
    result: dict[str, Any]
    guard_reasons: list[str]


def _guard(state: EmailState) -> EmailState:
    """Apply input guards and (when allowed) set the sanitized text.

    Args:
        state: Current graph state.

    Returns:
        Updated state with sanitized + guard_reasons fields.
    """
    decision = check_input(state["raw"])
    return {
        **state,
        "sanitized": decision.sanitized_text,
        "guard_reasons": list(decision.reasons),
        "result": {} if decision.allowed else {"category": "unknown"},
    }


def _extract(state: EmailState) -> EmailState:
    """Run structured extraction via the configured LLM.

    Skipped when guards already rejected the input.
    """
    if state.get("guard_reasons"):
        return state
    llm = get_chat_model().with_structured_output(EmailFields)
    fields: EmailFields = llm.invoke(
        "Extract fields from this email:\n" + state["sanitized"]
    )
    cleaned = check_output(fields.model_dump_json())
    return {**state, "result": EmailFields.model_validate_json(cleaned).model_dump()}


def build_email_parse_graph():
    """Compile the email parse graph.

    Returns:
        Compiled LangGraph app exposing ``invoke`` / ``stream``.
    """
    g = StateGraph(EmailState)
    g.add_node("guard", _guard)
    g.add_node("extract", _extract)
    g.set_entry_point("guard")
    g.add_edge("guard", "extract")
    g.add_edge("extract", END)
    return g.compile()
