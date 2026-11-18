from fastapi import FastAPI
from app.routes import invoices
from app.routes import payments
from app.routes import credit_ledger

app = FastAPI(title="beta_billing", version="0.1.0")

app.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(credit_ledger.router, prefix="/credit_ledger", tags=["credit_ledger"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "beta_billing"}