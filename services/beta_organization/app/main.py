from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError

from app.routes import auth, tenants, org_users, roles, subscriptions
from app.routes import ferti
from app.config import settings

app = FastAPI(
    title="Ferti+ API",
    version="1.0.0",
    docs_url="/api/docs" if settings.ENVIRONMENT.lower() != "production" else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if settings.ENVIRONMENT.lower() != "production" else None,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(self), geolocation=(), microphone=()",
        )
        if settings.ENVIRONMENT.lower() == "production":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; frame-ancestors 'none'; base-uri 'self'",
            )
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
app.include_router(org_users.router, prefix="/org_users", tags=["org_users"])
app.include_router(roles.router, prefix="/roles", tags=["roles"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
app.include_router(ferti.router)


@app.exception_handler(HTTPException)
async def http_problem(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "Request could not be completed."
    return JSONResponse(
        status_code=exc.status_code,
        media_type="application/problem+json",
        content={
            "type": "about:blank",
            "title": "Request failed",
            "status": exc.status_code,
            "detail": detail,
            "errors": [],
        },
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_problem(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(part) for part in item["loc"]), "message": item["msg"]}
        for item in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        media_type="application/problem+json",
        content={
            "type": "about:blank",
            "title": "Validation failed",
            "status": 422,
            "detail": "One or more request fields are invalid.",
            "errors": errors,
        },
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "beta_organization"}


@app.get("/version")
def version():
    return {"service": "ferti-api", "version": app.version}