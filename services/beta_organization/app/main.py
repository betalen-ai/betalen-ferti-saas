from fastapi import FastAPI
from app.routes import tenants
from app.routes import org_users
from app.routes import roles
from app.routes import subscriptions

app = FastAPI(title="beta_organization", version="0.1.0")

app.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
app.include_router(org_users.router, prefix="/org_users", tags=["org_users"])
app.include_router(roles.router, prefix="/roles", tags=["roles"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "beta_organization"}