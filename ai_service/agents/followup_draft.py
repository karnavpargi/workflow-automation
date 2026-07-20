"""FollowupDraftingAgent (RAG + HITL).

Retrieves past successful follow-up examples from a tenant-scoped
pgvector collection and asks the configured LLM to draft a new
message. The draft is stored as a Reminder with ``status=draft`` for
human-in-the-loop review; it is never sent from the AI service.
"""

from followups.services import create_draft_reminder  # noqa: F401  (re-export)


def retrieve_examples(tenant_id: int, *, k: int = 3) -> list[str]:
    """Pull the top-k most-recent successful follow-up texts for ``tenant_id``.

    Reads from the ``followups_successfulfollowup`` table (RLS-protected
    at the DB level — the agent's query is automatically scoped to the
    caller's tenant when RLS is on, and the explicit ``tenant=tenant_id``
    filter is the in-Python safety net for the test path where RLS
    is disabled).

    Args:
        tenant_id: Owning tenant PK.
        k: Number of examples to return.

    Returns:
        A list of past follow-up texts, newest first.
    """
    from followups.models import SuccessfulFollowup

    return list(
        SuccessfulFollowup.objects.filter(tenant_id=tenant_id)
        .order_by("-sent_at")
        .values_list("draft_text", flat=True)[:k]
    )


def draft_followup(
    *,
    tenant_id: int,
    invoice_number: str,
    due_date_iso: str,
    recipient_email: str,
) -> dict:
    """Draft a follow-up message and persist it as a DRAFT Reminder.

    Args:
        tenant_id: Owning tenant PK.
        invoice_number: The invoice being reminded about.
        due_date_iso: ISO-formatted due date for the prompt.
        recipient_email: Target recipient.

    Returns:
        A dict ``{"reminder_id": int, "draft_text": str}``.
    """
    from ai_service.llm.factory import get_chat_model

    examples = retrieve_examples(tenant_id)
    examples_block = "\n".join(f"- {e}" for e in examples) if examples else "(none)"
    prompt = (
        "Draft a short, friendly follow-up reminder for an invoice due soon.\n"
        f"Invoice: {invoice_number}\n"
        f"Due date: {due_date_iso}\n"
        f"Recipient: {recipient_email}\n"
        f"Past successful examples:\n{examples_block}\n"
        "Write only the message body."
    )
    draft_text = get_chat_model().invoke(prompt).content  # type: ignore[attr-defined]

    from tenants.models import Tenant

    tenant = Tenant.objects.get(pk=tenant_id)
    rem = create_draft_reminder(
        tenant=tenant,
        subject=f"Invoice {invoice_number} due",
        recipient_email=recipient_email,
        invoice_number=invoice_number,
        due_date_iso=due_date_iso,
        draft_text=str(draft_text),
    )
    return {"reminder_id": rem.id, "draft_text": str(draft_text)}
