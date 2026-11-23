import uuid
from decimal import Decimal

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects import postgresql

from app.main import app
from app.models import Farmer, Product
from app.routes.ferti import _owned, _pack_factor, _pdf_response, _xlsx_response, calculate_bill
from app.services.auth_service import create_access_token
from app.services.feature_flags import can_use


def test_free_plan_feature_flags_keep_core_features():
    assert can_use(None, "billing") is True
    assert can_use(None, "multiUser") is False


def test_pending_tenant_status_is_protected():
    from app.models.tenant import Tenant
    from app.routes.ferti import _tenant_status_error

    tenant = Tenant(status="PENDING_REVIEW", reference_no="FRT-2026-000123")
    error = _tenant_status_error(tenant)
    assert error is not None
    assert error.status_code == 403
    assert error.detail["code"] == "TENANT_PENDING_REVIEW"
    assert "under review" in error.detail["message"]


def test_access_tokens_expire_in_fifteen_minutes():
    token = create_access_token(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        email="owner@example.com",
        role="owner",
    )
    from jose import jwt
    claims = jwt.decode(token, "change_me_in_prod", algorithms=["HS256"])
    assert claims["exp"] - claims["iat"] == 15 * 60


def test_spot_bill_preview_applies_discount():
    result = calculate_bill({
        "paymentType": "SPOT",
        "items": [{"packId": "p1", "qty": 1, "unitPrice": "1000.00"}],
        "discount": {"type": "AMOUNT", "value": "50.00"},
    })

    assert result["total"] == "950.00"
    assert result["discount"] == "50.00"


def test_credit_bill_preview_calculates_interest():
    result = calculate_bill({
        "paymentType": "CREDIT",
        "items": [{"packId": "p1", "qty": 1, "unitPrice": "1000.00"}],
        "discount": {"type": "NONE"},
        "interest": {"ratePerMonth": "1.00", "months": "6"},
        "paidNow": "0.00",
    })

    assert result["interestAmount"] == "60.00"
    assert result["total"] == "1060.00"
    assert result["balance"] == "1060.00"


def test_part_bill_charges_interest_only_on_credit_amount():
    result = calculate_bill({
        "paymentType": "PART",
        "items": [{"packId": "p1", "qty": 1, "unitPrice": "1000.00"}],
        "discount": {"type": "NONE"},
        "interest": {"ratePerMonth": "1.00", "months": "6"},
        "paidNow": "400.00",
    })

    assert result["interestAmount"] == "36.00"
    assert result["total"] == "1036.00"
    assert result["balance"] == "636.00"


def test_pack_size_is_converted_to_product_base_unit():
    product = Product(unit_type="solid")

    assert _pack_factor(product, "500", "g") == Decimal("0.500")


def test_pack_rejects_units_for_a_different_product_type():
    product = Product(unit_type="liquid")

    with pytest.raises(HTTPException) as error:
        _pack_factor(product, "500", "g")

    assert error.value.status_code == 422


@pytest.mark.asyncio
async def test_owned_query_always_filters_by_tenant():
    class Result:
        def scalar_one_or_none(self):
            return None

    class Session:
        statement = None

        async def execute(self, statement):
            self.statement = statement
            return Result()

    tenant_id = uuid.uuid4()
    session = Session()

    with pytest.raises(HTTPException) as error:
        await _owned(session, Farmer, tenant_id, uuid.uuid4())

    compiled = session.statement.compile(dialect=postgresql.dialect())
    assert compiled.params["tenant_id_1"] == tenant_id
    assert error.value.status_code == 404


def test_api_is_mounted_under_versioned_path():
    paths = app.openapi()["paths"]
    assert "/api/v1/brands" in paths
    assert "/api/v1/products/{record_id}" in paths
    assert "/api/v1/bills/preview" in paths
    assert "/api/v1/stock/receipts" in paths
    assert "/api/v1/farmers/{farmer_id}/khata" in paths
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/otp/send" in paths
    assert "/api/v1/auth/otp/verify" in paths
    assert "/api/v1/auth/oauth/google" in paths
    assert "/api/v1/auth/forgot-password" in paths
    assert "/api/v1/auth/reset-password" in paths
    assert "/api/v1/auth/refresh" in paths
    assert "/api/v1/products/{product_id}/packs" in paths


def test_exports_are_valid_downloads():
    pdf = _pdf_response("Test", ["row"], "test.pdf")
    workbook = _xlsx_response("Test", ["column"], [["value"]], "test.xlsx")

    assert pdf.media_type == "application/pdf"
    assert pdf.body.startswith(b"%PDF-1.4")
    assert workbook.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert workbook.body.startswith(b"PK")


@pytest.mark.asyncio
async def test_bill_preview_is_available_through_authenticated_api():
    token = create_access_token(user_id=uuid.uuid4(), tenant_id=uuid.uuid4(), email="owner@example.com")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/bills/preview",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "paymentType": "SPOT",
                "items": [{"packId": "p1", "qty": 1, "unitPrice": "1000.00"}],
                "discount": {"type": "AMOUNT", "value": "50.00"},
            },
        )

    assert response.status_code == 200
    assert response.json()["total"] == "950.00"
