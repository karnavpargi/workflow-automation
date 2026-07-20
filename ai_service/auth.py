"""JWT verification shared with Django's ``SIMPLE_JWT``.

The Django backend mints HS256 tokens with the project's
``SECRET_KEY``; the AI service verifies the same secret via
``AI_JWT_SECRET``. Anyone holding a valid token can call protected
endpoints; the ``tenant_id`` claim is forwarded so downstream
endpoints can apply tenant scoping.
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ai_service.config import settings

_bearer = HTTPBearer(auto_error=True)


def current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),  # noqa: B008
) -> dict:
    """Decode the Bearer token and return the claims dict.

    Args:
        creds: Bearer credentials from the ``Authorization`` header.

    Returns:
        Claims dict (includes ``user_id`` and ``tenant_id`` when set).

    Raises:
        HTTPException: 401 if the token is missing, malformed, or
            signed with a different secret.
    """
    try:
        return jwt.decode(
            creds.credentials,
            settings.jwt_secret,
            algorithms=["HS256"],
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc
