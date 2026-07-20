"""Tests for the followups Celery task wrapper."""

from unittest.mock import patch

import pytest


@pytest.mark.django_db
def test_process_due_reminders_task_delegates_to_service():
    """The Celery task is a thin wrapper around services.process_due_reminders."""
    from followups import tasks

    with patch.object(tasks, "process_due_reminders", return_value=7) as svc:
        result = tasks.process_due_reminders_task()

    svc.assert_called_once_with()
    assert result == 7
