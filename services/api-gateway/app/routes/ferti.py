import os

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response

router = APIRouter()
ORG_SERVICE_URL = os.getenv("ORG_SERVICE_URL", "http://beta_organization:8001")
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


@router.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def forward_ferti_api(path: str, request: Request):
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }
    headers["x-forwarded-host"] = request.headers.get("host", "")
    headers["x-forwarded-proto"] = request.url.scheme
    url = f"{ORG_SERVICE_URL}/api/{path}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream = await client.request(
                request.method,
                url,
                params=request.query_params,
                headers=headers,
                content=await request.body(),
            )
    except httpx.HTTPError as exc:
        return Response(
            content=b'{"type":"about:blank","title":"Upstream unavailable","status":502,"detail":"The Ferti+ API service is unavailable.","errors":[]}',
            status_code=502,
            media_type="application/problem+json",
        )
    response_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )
