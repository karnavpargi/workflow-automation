# ruff: noqa: I001, F401
"""Tests for FollowupRule and Reminder models."""

from datetime import timedelta

import pytest
from django.utils import timezone


@pytest.mark.django_db
def test_create_followup_rule_with_defaults():
    """A FollowupRule stores channel/offset/template and FKs a tenant."""
    from followups.models import FollowupRule
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    rule = FollowupRule.objects.create(
        tenant=t,
        name="Invoice 7d before",
        channel=FollowupRule.Channel.EMAIL,
        offset_days=-7,
        template="Heads up: {subject} is due {due_date}.",
    )
    assert rule.tenant_id == t.id
    assert rule.channel == "email"
    assert rule.offset_days == -7
    assert "{subject}" in rule.template


@pytest.mark.django_db
def test_create_reminder_defaults_to_pending():
    """A new Reminder is PENDING and stores due_at + context for the template."""
    from followups.models import Reminder
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    due = timezone.now() + timedelta(days=3)
    rem = Reminder.objects.create(
        tenant=t,
        subject="INV-1 due",
        due_at=due,
        recipient_email="client@x.io",
        context={"subject": "Invoice INV-1", "due_date": "2026-08-01"},
    )
    assert rem.status == Reminder.Status.PENDING
    assert rem.status == "pending"
    assert rem.due_at == due
    assert rem.context["subject"] == "Invoice INV-1"


@pytest.mark.django_db
def test_reminder_rule_is_optional():
    """A Reminder can exist without a rule (ad-hoc reminders)."""
    from followups.models import Reminder
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    rem = Reminder.objects.create(
        tenant=t,
        subject="Manual ping",
        due_at=timezone.now(),
        recipient_email="x@y.io",
    )
    assert rem.rule is None


@pytest.mark.django_db
def test_followup_rule_delete_leaves_reminder_intact():
    """Deleting a FollowupRule nulls the rule on Reminder (SET_NULL)."""
    from followups.models import FollowupRule, Reminder
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    rule = FollowupRule.objects.create(
        tenant=t, name="R", channel="email", offset_days=-3
    )
    rem = Reminder.objects.create(
        tenant=t, subject="S", due_at=timezone.now(), rule=rule
    )
    rule.delete()
    rem.refresh_from_db()
    assert rem.rule is None
    assert rem.subject == "S"
