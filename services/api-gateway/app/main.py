import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(title="api-gateway", version="0.1.0")

# 1. Global CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200", 
        "http://127.0.0.1:4200", 
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Service Routing Map using settings
SERVICES = {
    # Organization Service
    "auth": settings.ORG_SERVICE_URL,
    "tenants": settings.ORG_SERVICE_URL,
    "org_users": settings.ORG_SERVICE_URL,
    "roles": settings.ORG_SERVICE_URL,
    "subscriptions": settings.ORG_SERVICE_URL,
    
    # Billing Service
    "invoices": settings.BILLING_SERVICE_URL,
    "payments": settings.BILLING_SERVICE_URL,
    "credit_ledger": settings.BILLING_SERVICE_URL,
    
    # Inventory Service
    "products": settings.INVENTORY_SERVICE_URL,
    "warehouses": settings.INVENTORY_SERVICE_URL,
    "stock": settings.INVENTORY_SERVICE_URL,
}

HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length"
}

@app.api_route("/api/v1/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def reverse_proxy(service: str, path: str, request: Request):
    """Dynamically route requests to the correct microservice."""
    
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Unknown service route: {service}")
        
    target_base_url = SERVICES[service]
    url = f"{target_base_url}/api/v1/{service}/{path}"
    
    headers = {
        key: value for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }

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

    response_headers = {
        key: value for key, value in upstream.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }
    
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )

@app.get("/health")
def health():
    return {"status": "ok", "service": "api-gateway", "environment": settings.ENVIRONMENT}
