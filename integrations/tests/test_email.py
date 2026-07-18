"""Tests for Django SMTP email adapter."""

import pytest
from django.core import mail

from integrations.email.django_smtp import DjangoSmtpEmailAdapter


@pytest.mark.django_db
def test_send_uses_django_outbox(settings):
    """EmailAdapter.send deposits a message in the locmem outbox."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    adapter = DjangoSmtpEmailAdapter({})
    adapter.send(to=["a@x.io"], subject="Hi", body="Hello")
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Hi"
