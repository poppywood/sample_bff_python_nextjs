from __future__ import annotations

from contextlib import asynccontextmanager
from urllib.parse import urlencode

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from redis.asyncio import Redis
from starlette.middleware.sessions import SessionMiddleware

from .auth import oauth
from .config import get_settings
from .proxy import proxy_request
from .security import extract_roles, generate_csrf_token, generate_session_id, load_private_key, require_csrf
from .sessions import SessionStore

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_private_key()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    await redis.ping()
    app.state.redis = redis
    app.state.sessions = SessionStore(redis)
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=5.0, read=10.0, write=10.0, pool=5.0)
    )
    try:
        yield
    finally:
        await app.state.http_client.aclose()
        await redis.aclose()


app = FastAPI(title="sample-bff", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.oauth_state_secret,
    https_only=settings.session_secure_cookies,
    same_site="lax",
    session_cookie="bff_oauth_state",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)


def get_session_store(request: Request) -> SessionStore:
    return request.app.state.sessions


async def get_current_session(
    request: Request,
    session_store: SessionStore = Depends(get_session_store),
) -> dict[str, object]:
    session_id = request.cookies.get(settings.session_cookie_name)
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session = await session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")

    request.state.session_id = session_id
    return session


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/auth/login")
async def auth_login(request: Request):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.auth0.authorize_redirect(request, redirect_uri)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.auth0.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo:
        response = await oauth.auth0.get("userinfo", token=token)
        userinfo = response.json()

    session_id = generate_session_id()
    csrf_token = generate_csrf_token()
    session_payload = {
        "user_id": userinfo["sub"],
        "email": userinfo.get("email"),
        "name": userinfo.get("name") or userinfo.get("nickname") or userinfo.get("email"),
        "picture": userinfo.get("picture"),
        "roles": extract_roles(userinfo, settings.auth0_roles_claim),
        "csrf_token": csrf_token,
    }
    await request.app.state.sessions.save(session_id, session_payload, settings.session_ttl_seconds)

    redirect_response = RedirectResponse(url=f"{settings.frontend_origin}/dashboard", status_code=status.HTTP_302_FOUND)
    redirect_response.set_cookie(
        key=settings.session_cookie_name,
        value=session_id,
        httponly=True,
        secure=settings.session_secure_cookies,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
        path="/",
    )
    return redirect_response


@app.post("/auth/logout")
async def auth_logout(
    request: Request,
    session: dict[str, object] = Depends(get_current_session),
    session_store: SessionStore = Depends(get_session_store),
):
    require_csrf(request, session)
    await session_store.delete(request.state.session_id)
    logout_url = "https://{domain}/v2/logout?{query}".format(
        domain=settings.auth0_domain,
        query=urlencode({"client_id": settings.auth0_client_id, "returnTo": settings.frontend_origin}),
    )
    response = JSONResponse({"logout_url": logout_url})
    response.delete_cookie(settings.session_cookie_name, path="/")
    return response


@app.get("/me")
async def me(session: dict[str, object] = Depends(get_current_session)):
    return {
        "user": {
            "id": session["user_id"],
            "email": session.get("email"),
            "name": session.get("name"),
            "picture": session.get("picture"),
            "roles": session.get("roles", []),
        },
        "csrfToken": session.get("csrf_token"),
    }


@app.api_route("/api/service-a/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def service_a_proxy(
    path: str,
    request: Request,
    session: dict[str, object] = Depends(get_current_session),
):
    require_csrf(request, session)
    return await proxy_request(request, settings.service_a_base_url, path, session)
