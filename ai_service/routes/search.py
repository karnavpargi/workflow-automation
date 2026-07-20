"""Placeholder for the search router (Plan 9 implements the endpoints)."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/_stub")
def search_stub() -> dict[str, str]:
    """Plan 9 will replace this with vector search and filter endpoints.

    Returns:
        Static stub response.
    """
    return {"status": "stub", "plan": "9"}
