from fastapi import FastAPI
from app.routes import dashboards
from app.routes import exports

app = FastAPI(title="beta_reports", version="0.1.0")

app.include_router(dashboards.router, prefix="/api/v1/dashboards", tags=["dashboards"])
app.include_router(exports.router, prefix="/api/v1/exports", tags=["exports"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "beta_reports"}