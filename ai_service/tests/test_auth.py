"""JWT auth tests.

The AI service shares a secret with Django's ``SIMPLE_JWT`` so a token
minted by the main app verifies here. These tests use ``python-jose``
to mint tokens with the same algorithm + secret.
"""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jose import jwt

from ai_service.auth import current_user
from ai_service.config import settings


def _mint(secret: str, *, exp_delta: timedelta = timedelta(minutes=5)) -> str:
    """Mint an HS256 JWT with ``user_id`` and ``tenant_id`` claims."""
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "user_id": 1,
            "tenant_id": 42,
            "iat": int(now.timestamp()),
            "exp": int((now + exp_delta).timestamp()),
        },
        secret,
        algorithm="HS256",
    )


def _build_app() -> FastAPI:
    """Build a tiny FastAPI app whose only job is to exercise auth."""
    app = FastAPI()

    @app.get("/_whoami")
    def whoami(claims: dict = Depends(current_user)) -> dict:  # noqa: B008
        return {"sub": claims.get("user_id"), "tenant": claims.get("tenant_id")}

    return app


@pytest.fixture
def app_client():
    """A TestClient bound to the tiny auth-only app."""
    return TestClient(_build_app())


def test_current_user_returns_claims_for_valid_token(app_client):
    """A JWT signed with the configured secret decodes to its claims."""
    token = _mint(settings.jwt_secret)
    r = app_client.get("/_whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == {"sub": 1, "tenant": 42}


def test_current_user_rejects_missing_token(app_client):
    """No Authorization header returns 403 (HTTPBearer default)."""
    r = app_client.get("/_whoami")
    assert r.status_code in (401, 403)


def test_current_user_rejects_wrong_secret(app_client):
    """A token signed with a different secret is rejected as invalid."""
    token = _mint("not-the-real-secret")
    r = app_client.get("/_whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert "invalid" in r.json()["detail"].lower()


def test_current_user_rejects_expired_token(app_client):
    """An expired token is rejected with 401."""
    token = _mint(settings.jwt_secret, exp_delta=timedelta(seconds=-10))
    r = app_client.get("/_whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
