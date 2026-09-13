from __future__ import annotations

from authlib.integrations.starlette_client import OAuth

from .config import get_settings

settings = get_settings()

oauth = OAuth()
oauth.register(
    name="auth0",
    client_id=settings.auth0_client_id,
    client_secret=settings.auth0_client_secret,
    server_metadata_url=f"https://{settings.auth0_domain}/.well-known/openid-configuration",
    client_kwargs={"scope": "openid profile email"},
)
