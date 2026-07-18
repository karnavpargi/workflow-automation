"""Workflow-specific exceptions."""


class RetryableError(Exception):
    """Transient failure; Celery should retry with backoff."""


class PermanentError(Exception):
    """Non-retryable failure; mark task dead immediately."""


class HandlerNotFound(Exception):
    """No handler registered for the event name."""
