from fastapi import FastAPI

from app.routes import (
    audit_logs,
    auth,
    bills,
    brands,
    cashbook,
    categories,
    farmers,
    khata,
    org_users,
    packs,
    payments,
    products,
    roles,
    seasons,
    settings,
    stock_lots,
    stock_movements,
    subscriptions,
    tenants,
)

app = FastAPI(title="beta_organization", version="0.1.0")

# Core org routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["tenants"])
app.include_router(org_users.router, prefix="/api/v1/org_users", tags=["org_users"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["roles"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])

# Shop / ferti routes (each router already defines its own prefix & tag)
app.include_router(brands.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(packs.router, prefix="/api/v1")
app.include_router(farmers.router, prefix="/api/v1")
app.include_router(seasons.router, prefix="/api/v1")
app.include_router(cashbook.router, prefix="/api/v1")
app.include_router(bills.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(khata.router, prefix="/api/v1")
app.include_router(audit_logs.router, prefix="/api/v1")
app.include_router(stock_lots.router, prefix="/api/v1")
app.include_router(stock_movements.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "beta_organization"}