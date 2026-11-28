from fastapi import APIRouter, HTTPException

from app.config import settings
from app.services.renderer import Renderer, TEMPLATES
from app.services.email_service import validate_template

router = APIRouter()


@router.get("/templates")
def list_templates():
    fields = {
        "PASSWORD_RESET_REQUESTED": ["ownerName", "resetLink", "expiresInMinutes", "requestedAt", "requestIp", "deviceDescription"],
        "PASSWORD_CHANGED": ["ownerName", "changedAt", "changeType", "ip", "deviceDescription", "location", "secureAccountLink", "supportEmail"],
        "LOGIN_FAILED_ALERT": ["ownerName", "attemptCount", "lastAttemptAt", "ip", "deviceDescription", "method", "locked", "lockedUntil", "resetPasswordLink"],
        "ONBOARDING_APPROVED": ["ownerName", "shopName", "tenantId", "referenceNo", "approvedAt", "signInUrl", "loginEmail", "supportEmail", "helpCenterUrl"],
    }
    return {"templates": [
        {"name": name, "subject": subject, "requiredFields": fields[name], "locales": ["en", "te", "hi"]}
        for name, (subject, _) in TEMPLATES.items()
    ]}


@router.post("/templates/{name}/preview")
def preview_template(name: str, data: dict, recipientName: str | None = None):
    if settings.ENV == "production":
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Preview disabled in production"})
    validated = validate_template(name, data)
    subject, html, text = Renderer().render(name, "en", validated, recipientName)
    return {"subject": subject, "html": html, "text": text}
