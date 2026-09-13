from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4

import jwt
from fastapi import HTTPException, Request, status

from .config import get_settings


@lru_cache(maxsize=1)
def load_private_key() -> str:
    settings = get_settings()
    return Path(settings.internal_jwt_private_key_path).read_text(encoding="utf-8")


def generate_session_id() -> str:
    return secrets.token_urlsafe(32)


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def extract_roles(userinfo: dict[str, Any], claim_name: str) -> list[str]:
    roles = userinfo.get(claim_name) or userinfo.get("roles") or []
    if isinstance(roles, list):
        return [str(role) for role in roles]
    return []


def mint_service_token(session: dict[str, Any]) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "iss": settings.internal_jwt_issuer,
        "aud": settings.internal_jwt_audience,
        "sub": session["user_id"],
        "email": session.get("email"),
        "roles": session.get("roles", []),
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, load_private_key(), algorithm="RS256")


def require_csrf(request: Request, session: dict[str, Any]) -> None:
    if request.method.upper() not in {"POST", "PUT", "PATCH", "DELETE"}:
        return

    csrf_header = request.headers.get("x-csrf-token")
    if not csrf_header or csrf_header != session.get("csrf_token"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
