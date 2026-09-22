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

# Used when no (valid) bearer token is presented, so the JWT decode/verification
# path below always runs and takes a comparable amount of time whether or not a
# token was supplied. This avoids a timing side channel that could let a caller
# distinguish "no token sent" from "token sent but invalid" via response latency.
_DUMMY_TOKEN = jwt.encode({"sub": "anonymous"}, "dummy-signing-secret-not-used-for-verification", algorithm="HS256")


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
        os.getenv("INTERNAL_JWT_AUDIENCE", ""),
    )


async def require_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    has_bearer_token = credentials is not None and credentials.scheme.lower() == "bearer"
    token = credentials.credentials if has_bearer_token else _DUMMY_TOKEN

    issuer, audience = _settings()
    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            _load_public_key(),
            algorithms=["RS256"],
            issuer=issuer,
            audience=audience,
            options={"require": ["exp", "iat", "nbf", "iss", "aud", "sub", "jti"]},
        )
        if not has_bearer_token:
            # Never reachable with a valid signature since _DUMMY_TOKEN is signed
            # with an unrelated secret, but keeps the control flow explicit.
            raise jwt.InvalidTokenError("Missing bearer token")
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token") from exc

    return AuthenticatedUser(
        sub=str(claims["sub"]),
        email=claims.get("email"),
        roles=[str(role) for role in claims.get("roles", [])],
    )
