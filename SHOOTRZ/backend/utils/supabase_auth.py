from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header, HTTPException

from ..storage.supabase_client import get_anon_client


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    email: Optional[str] = None


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    return parts[1].strip()


def get_authenticated_user(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> AuthenticatedUser:
    """
    Validates a Supabase access token and returns the authenticated user identity.

    The client must pass: Authorization: Bearer <supabase_access_token>
    """
    token = _extract_bearer_token(authorization)

    try:
        sb = get_anon_client()
        # supabase-py v2: auth.get_user(jwt=token)
        res = sb.auth.get_user(jwt=token)  # type: ignore[call-arg]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    user = getattr(res, "user", None)
    if not user or not getattr(user, "id", None):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return AuthenticatedUser(user_id=user.id, email=getattr(user, "email", None))


def get_authenticated_user_id(
    user: AuthenticatedUser = Depends(get_authenticated_user),
) -> str:
    return user.user_id




