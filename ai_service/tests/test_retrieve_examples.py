"""Tests for the ``retrieve_examples`` RAG helper + ``approve_draft``.

The :func:`ai_service.agents.followup_draft.retrieve_examples`
function reads the most-recent N ``SuccessfulFollowup`` rows for the
tenant. ``approve_draft`` flips a DRAFT reminder to PENDING *and*
records a ``SuccessfulFollowup`` so the next draft benefits from
this one as a positive example.
"""

from datetime import timedelta

import pytest
from django.utils import timezone


def _tenant(slug: str = "a"):
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email=f"a@{slug}.io", password="p", username=slug)
    return tsvc.create_tenant(name=slug.upper(), slug=slug, admin=u)


@pytest.mark.django_db
def test_retrieve_examples_returns_recent_successful_for_tenant():
    """Top-3 by ``sent_at desc`` for the caller's tenant only."""
    from ai_service.agents.followup_draft import retrieve_examples
    from followups.models import SuccessfulFollowup

    t = _tenant()
    now = timezone.now()
    # Create rows; auto_now_add fires so we then ``update`` to set
    # distinct sent_at values (the spec orders by -sent_at).
    rows = SuccessfulFollowup.objects.bulk_create(
        [
            SuccessfulFollowup(tenant=t, draft_text="recent-1"),
            SuccessfulFollowup(tenant=t, draft_text="recent-2"),
            SuccessfulFollowup(tenant=t, draft_text="old"),
        ]
    )
    SuccessfulFollowup.objects.filter(pk=rows[0].pk).update(
        sent_at=now - timedelta(seconds=10)
    )
    SuccessfulFollowup.objects.filter(pk=rows[1].pk).update(
        sent_at=now - timedelta(seconds=20)
    )
    SuccessfulFollowup.objects.filter(pk=rows[2].pk).update(
        sent_at=now - timedelta(days=1)
    )
    examples = retrieve_examples(t.id, k=2)
    assert examples == ["recent-1", "recent-2"]


@pytest.mark.django_db
def test_retrieve_examples_isolates_per_tenant():
    """Other tenants' successful followups are not visible."""
    from ai_service.agents.followup_draft import retrieve_examples
    from followups.models import SuccessfulFollowup

    t1 = _tenant("a")
    t2 = _tenant("b")
    SuccessfulFollowup.objects.create(tenant=t1, draft_text="A-ex")
    SuccessfulFollowup.objects.create(tenant=t2, draft_text="B-ex")
    assert retrieve_examples(t1.id, k=5) == ["A-ex"]
    assert retrieve_examples(t2.id, k=5) == ["B-ex"]


@pytest.mark.django_db
def test_approve_draft_creates_successful_followup():
    """Approving a DRAFT reminder records a ``SuccessfulFollowup``."""
    from followups.models import Reminder, SuccessfulFollowup
    from followups.services import approve_draft

    t = _tenant()
    rem = Reminder.objects.create(
        tenant=t,
        subject="INV-X",
        due_at=timezone.now() + timedelta(days=1),
        recipient_email="x@y.io",
        status=Reminder.Status.DRAFT,
        draft_text="please pay soon",
    )
    approve_draft(rem)
    rem.refresh_from_db()
    assert rem.status == Reminder.Status.PENDING
    assert SuccessfulFollowup.objects.filter(reminder=rem).exists()


@pytest.mark.django_db
def test_approve_draft_noop_on_non_draft():
    """Approving a non-draft reminder does not create a SuccessfulFollowup."""
    from followups.models import Reminder, SuccessfulFollowup
    from followups.services import approve_draft

    t = _tenant()
    rem = Reminder.objects.create(
        tenant=t,
        subject="already-pending",
        due_at=timezone.now() + timedelta(days=1),
        status=Reminder.Status.PENDING,
        draft_text="",
    )
    approve_draft(rem)
    assert not SuccessfulFollowup.objects.exists()
