"""Map event names to handler callables."""

from collections.abc import Callable
from typing import Any

from workflows.exceptions import HandlerNotFound

_HANDLERS: dict[str, Callable[..., Any]] = {}


def register(event_name: str, handler: Callable[..., Any]) -> None:
    """Register a handler for an event name.

    Args:
        event_name: Dotted event name.
        handler: Callable receiving the Event instance.
    """
    _HANDLERS[event_name] = handler


def get(event_name: str) -> Callable[..., Any]:
    """Return the handler for ``event_name``.

    Args:
        event_name: Dotted event name.

    Returns:
        The registered callable.

    Raises:
        HandlerNotFound: if nothing is registered.
    """
    try:
        return _HANDLERS[event_name]
    except KeyError as exc:
        raise HandlerNotFound(event_name) from exc
