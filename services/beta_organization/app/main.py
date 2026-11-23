from fastapi import FastAPI
from app.routes import auth, tenants, org_users, roles, subscriptions

app = FastAPI(
    title="beta_organization",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["tenants"])
app.include_router(org_users.router, prefix="/api/v1/org_users", tags=["org_users"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["roles"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "beta_organization"}
