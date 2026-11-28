import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings  # or wherever your Settings class lives

app = FastAPI(title="api-gateway", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ORG_URL = settings.ORG_SERVICE_URL
BILLING_URL = settings.BILLING_SERVICE_URL
INVENTORY_URL = settings.INVENTORY_SERVICE_URL

SERVICES = {
    # Core org routes -> beta_organization:8001
    "auth": ORG_URL,
    "tenants": ORG_URL,
    "org_users": ORG_URL,
    "roles": ORG_URL,
    "subscriptions": ORG_URL,

    # Shop / ferti routes -> beta_organization:8001
    "brands": ORG_URL,
    "categories": ORG_URL,
    "products": ORG_URL,
    "packs": ORG_URL,
    "farmers": ORG_URL,
    "seasons": ORG_URL,
    "cashbook": ORG_URL,
    "bills": ORG_URL,
    "payments": ORG_URL,
    "khata": ORG_URL,
    "audit-logs": ORG_URL,
    "stock-lots": ORG_URL,
    "stock-movements": ORG_URL,
    "settings": ORG_URL,

    # Other microservices
    "invoices": BILLING_URL,
    "credit_ledger": BILLING_URL,
    "warehouses": INVENTORY_URL,
    "stock": INVENTORY_URL,
}

HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
}


@app.api_route("/api/v1/{service}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@app.api_route("/api/v1/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def reverse_proxy(service: str, request: Request, path: str = ""):
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Unknown service route: {service}")

    target_base_url = SERVICES[service].rstrip("/")
    clean_path = path.strip("/")
    service_path = f"/api/v1/{service}/{clean_path}" if clean_path else f"/api/v1/{service}"
    url = f"{target_base_url}{service_path}"

    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream = await client.request(
                request.method,
                url,
                params=request.query_params,
                headers=headers,
                content=await request.body(),
            )
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail=f"Service {service} is unavailable.")

    response_headers = {k: v for k, v in upstream.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "api-gateway"}