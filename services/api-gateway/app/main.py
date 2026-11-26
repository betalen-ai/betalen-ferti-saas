import os
import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="api-gateway", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICES = {
    "auth": os.getenv("ORG_SERVICE_URL", "http://beta_organization:8001"),
    "tenants": os.getenv("ORG_SERVICE_URL", "http://beta_organization:8001"),
    "org_users": os.getenv("ORG_SERVICE_URL", "http://beta_organization:8001"),
    "roles": os.getenv("ORG_SERVICE_URL", "http://beta_organization:8001"),
    "subscriptions": os.getenv("ORG_SERVICE_URL", "http://beta_organization:8001"),
    "invoices": os.getenv("BILLING_SERVICE_URL", "http://beta_billing:8002"),
    "payments": os.getenv("BILLING_SERVICE_URL", "http://beta_billing:8002"),
    "credit_ledger": os.getenv("BILLING_SERVICE_URL", "http://beta_billing:8002"),
    "products": os.getenv("INVENTORY_SERVICE_URL", "http://beta_inventory:8003"),
    "warehouses": os.getenv("INVENTORY_SERVICE_URL", "http://beta_inventory:8003"),
    "stock": os.getenv("INVENTORY_SERVICE_URL", "http://beta_inventory:8003"),
}

HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length"
}

@app.api_route("/api/v1/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def reverse_proxy(service: str, path: str, request: Request):
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Unknown service route: {service}")
        
    target_base_url = SERVICES[service]
    url = f"{target_base_url}/api/v1/{service}/{path}"
    
    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream = await client.request(
                request.method, url, params=request.query_params,
                headers=headers, content=await request.body(),
            )
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail=f"Service {service} is unavailable.")

    response_headers = {k: v for k, v in upstream.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}
    return Response(
        content=upstream.content, status_code=upstream.status_code,
        headers=response_headers, media_type=upstream.headers.get("content-type"),
    )

@app.get("/health")
def health():
    return {"status": "ok", "service": "api-gateway"}
