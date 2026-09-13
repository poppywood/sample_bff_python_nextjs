from __future__ import annotations

from typing import Iterable

import httpx
from fastapi import HTTPException, Request, Response, status

from .security import mint_service_token

REQUEST_HEADER_ALLOWLIST = {"accept", "content-type"}
RESPONSE_HEADER_DENYLIST = {
    "content-length",
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def _forward_headers(request: Request) -> dict[str, str]:
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() in REQUEST_HEADER_ALLOWLIST
    }
    return headers


def _response_headers(headers: Iterable[tuple[str, str]]) -> dict[str, str]:
    return {
        key: value
        for key, value in headers
        if key.lower() not in RESPONSE_HEADER_DENYLIST
    }


async def proxy_request(
    request: Request,
    service_base_url: str,
    path: str,
    session: dict[str, object],
    audience: str,
) -> Response:
    client: httpx.AsyncClient = request.app.state.http_client
    upstream_url = f"{service_base_url}/{path.lstrip('/')}"
    body = await request.body()
    headers = _forward_headers(request)
    headers["authorization"] = "Bearer " + mint_service_token(session, audience)

    try:
        upstream_response = await client.request(
            request.method,
            upstream_url,
            params=request.query_params.multi_items(),
            headers=headers,
            content=body or None,
        )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timed out while contacting downstream service",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to contact downstream service",
        ) from exc

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=_response_headers(upstream_response.headers.items()),
    )
