from app.services.email_service import validate_template


def test_onboarding_validation_accepts_required_data():
    data = validate_template("ONBOARDING_APPROVED", {
        "ownerName": "Ramesh",
        "shopName": "Sri Lakshmi Agro",
        "tenantId": "tenant-1",
        "referenceNo": "FRT-2026-000123",
        "approvedAt": "2026-11-26T10:15:00Z",
        "signInUrl": "https://app.ferti.example/signin",
        "loginEmail": "ramesh@example.com",
        "supportEmail": "support@ferti.example",
    })
    assert data["tenantId"] == "tenant-1"
