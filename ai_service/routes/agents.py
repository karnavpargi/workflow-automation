"""Placeholder for the agents router (Plan 9 implements the endpoints)."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/_stub")
def agents_stub() -> dict[str, str]:
    """Plan 9 will replace this with the agent execution endpoints.

    Returns:
        Static stub response.
    """
    return {"status": "stub", "plan": "9"}
