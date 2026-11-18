import os
import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_claims
from app.schemas.auth import LoginRequest, TokenResponse, MeResponse

router = APIRouter()

ORG_SERVICE_URL = os.getenv("ORG_SERVICE_URL", "http://beta_organization:8001")


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(f"{ORG_SERVICE_URL}/auth/login", json=payload.model_dump())
        
    if r.status_code != 200:
        try:
            detail = r.json().get("detail", "login_failed")
        except Exception:
            detail = r.text or "unknown_error_from_org_service"
            
        raise HTTPException(status_code=r.status_code, detail=detail)
        
    return r.json()


@router.get("/me", response_model=MeResponse)
async def me(claims: dict = Depends(get_current_claims)):
    return MeResponse(user_id=claims["sub"], tenant_id=claims["tid"], email=claims["email"])
