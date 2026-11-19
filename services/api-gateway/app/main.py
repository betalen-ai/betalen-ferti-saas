from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth
from app.routes import proxy

app = FastAPI(title="api-gateway", version="0.1.0")

# Explicitly allow the Angular and React apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(proxy.router, prefix="/proxy", tags=["proxy"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "api-gateway"}