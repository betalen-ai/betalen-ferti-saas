from fastapi import FastAPI
from app.routes import dashboards
from app.routes import exports

app = FastAPI(title="beta_reports", version="0.1.0")

app.include_router(dashboards.router, prefix="/dashboards", tags=["dashboards"])
app.include_router(exports.router, prefix="/exports", tags=["exports"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "beta_reports"}