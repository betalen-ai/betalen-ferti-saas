from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request

from app.routes import auth
from app.routes import proxy, ferti

app = FastAPI(title="api-gateway", version="0.1.0")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(self), geolocation=(), microphone=()",
    )
    return response

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
app.include_router(ferti.router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "api-gateway"}


@app.get("/version")
def version():
    return {"service": "api-gateway", "version": app.version}