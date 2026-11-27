from fastapi import FastAPI

from app.routes import auth, tenants, org_users, roles, subscriptions, ferti

app = FastAPI(title="beta_organization", version="0.1.0")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["tenants"])
app.include_router(org_users.router, prefix="/api/v1/org_users", tags=["org_users"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["roles"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])

# Ferti endpoints: /api/ferti/brands, /api/ferti/products, /api/ferti/stock-lots, etc.
app.include_router(ferti.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "beta_organization"}
