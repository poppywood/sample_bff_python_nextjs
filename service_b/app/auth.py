from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    sub: str
    email: str | None = None
    roles: list[str] = Field(default_factory=list)


@lru_cache(maxsize=1)
def _load_public_key() -> str:
    return Path(os.getenv("INTERNAL_JWT_PUBLIC_KEY_PATH", "keys/internal_public.pem")).read_text(encoding="utf-8")


def _settings() -> tuple[str, str]:
    return (
        os.getenv("INTERNAL_JWT_ISSUER", "sample-bff"),
        os.getenv("INTERNAL_JWT_AUDIENCE", "service-b"),
    )


async def require_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    issuer, audience = _settings()
    try:
        claims: dict[str, Any] = jwt.decode(
            credentials.credentials,
            _load_public_key(),
            algorithms=["RS256"],
            issuer=issuer,
            audience=audience,
            options={"require": ["exp", "iat", "nbf", "iss", "aud", "sub", "jti"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token") from exc

    return AuthenticatedUser(
        sub=str(claims["sub"]),
        email=claims.get("email"),
        roles=[str(role) for role in claims.get("roles", [])],
    )
