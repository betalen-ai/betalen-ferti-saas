from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth

app = FastAPI(title="api-gateway", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gateway exposes this at /api/v1/auth
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "api-gateway"}
