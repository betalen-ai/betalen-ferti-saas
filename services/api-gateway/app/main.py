from fastapi import FastAPI
from app.routes import auth
from app.routes import proxy

app = FastAPI(title="api-gateway", version="0.1.0")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(proxy.router, prefix="/proxy", tags=["proxy"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "api-gateway"}