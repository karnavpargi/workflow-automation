"""Tests for the handler registry."""

import pytest

from workflows import registry
from workflows.exceptions import HandlerNotFound


def test_register_and_get_handler():
    """Registered handlers are retrievable by event name."""

    def h(event):  # noqa: ANN001
        return "ok"

    registry.register("client.created", h)
    assert registry.get("client.created") is h


def test_get_missing_raises():
    """Missing handler raises HandlerNotFound."""
    with pytest.raises(HandlerNotFound):
        registry.get("does.not.exist")
