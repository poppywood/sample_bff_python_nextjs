from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


@dataclass(frozen=True)
class Settings:
    auth0_domain: str
    auth0_client_id: str
    auth0_client_secret: str
    auth0_roles_claim: str
    frontend_origin: str
    bff_base_url: str
    redis_url: str
    session_cookie_name: str
    session_cookie_domain: str | None
    session_ttl_seconds: int
    session_secure_cookies: bool
    oauth_state_secret: str
    internal_jwt_private_key_path: str
    internal_jwt_issuer: str
    internal_jwt_audience: str
    service_a_base_url: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        auth0_domain=os.getenv("AUTH0_DOMAIN", "example.auth0.com"),
        auth0_client_id=os.getenv("AUTH0_CLIENT_ID", "dev-client-id"),
        auth0_client_secret=os.getenv("AUTH0_CLIENT_SECRET", "dev-client-secret"),
        auth0_roles_claim=os.getenv("AUTH0_ROLES_CLAIM", "https://example.com/roles"),
        frontend_origin=os.getenv("FRONTEND_ORIGIN", "http://localhost:3000").rstrip("/"),
        bff_base_url=os.getenv("BFF_BASE_URL", "http://localhost:8000").rstrip("/"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        session_cookie_name=os.getenv("SESSION_COOKIE_NAME", "bff_session"),
        session_cookie_domain=os.getenv("SESSION_COOKIE_DOMAIN") or None,
        session_ttl_seconds=_get_int("SESSION_TTL_SECONDS", 60 * 60 * 8),
        session_secure_cookies=_get_bool("SESSION_SECURE_COOKIES", False),
        oauth_state_secret=os.getenv("OAUTH_STATE_SECRET", ""),
        internal_jwt_private_key_path=os.getenv("INTERNAL_JWT_PRIVATE_KEY_PATH", "keys/internal_private.pem"),
        internal_jwt_issuer=os.getenv("INTERNAL_JWT_ISSUER", "sample-bff"),
        internal_jwt_audience=os.getenv("INTERNAL_JWT_AUDIENCE", "service-a"),
        service_a_base_url=os.getenv("SERVICE_A_BASE_URL", "http://localhost:8001").rstrip("/"),
    )
