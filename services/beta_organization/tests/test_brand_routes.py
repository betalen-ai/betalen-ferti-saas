import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

from app.deps import CurrentUser
from app.main import app
from app.routes.ferti import _resolve_brand_tenant, list_brands
from app.schemas.ferti import BrandCreate, BrandOut, BrandUpdate


def test_brand_routes_are_mounted():
    paths = app.openapi()["paths"]
    assert "/api/v1/brands" in paths
    assert "/api/v1/brands/{brand_id}" in paths


def test_brand_create_schema_matches_frontend_fields_and_rejects_tenant_input():
    brand = BrandCreate(
        name=" Kisan Gold ",
        manufacturer=" Kisan Agro ",
        notes=" ",
        active=True,
    )
    assert brand.model_dump() == {
        "tenant_id": None,
        "name": "Kisan Gold",
        "manufacturer": "Kisan Agro",
        "notes": "",
        "active": True,
    }

    with pytest.raises(ValueError):
        BrandCreate(name="Kisan Gold", unexpected="value")


@pytest.mark.asyncio
async def test_brand_list_query_is_scoped_to_authenticated_tenant():
    class Result:
        def scalars(self):
            return self

        def all(self):
            return []

    class Session:
        statement = None

        async def execute(self, statement):
            self.statement = statement
            return Result()

    tenant_id = uuid.uuid4()
    session = Session()
    await list_brands(
        tenant_id=None,
        include_inactive=False,
        limit=100,
        offset=0,
        cu=CurrentUser(user_id=uuid.uuid4(), tenant_id=tenant_id, role="OWNER"),
        db=session,
    )
    compiled = session.statement.compile(dialect=postgresql.dialect())
    assert tenant_id in compiled.params.values()


def test_brand_output_includes_tenant_id():
    assert "tenant_id" in BrandOut.model_fields


def test_brand_write_schemas_include_tenant_id():
    tenant_id = uuid.uuid4()
    create = BrandCreate(name="Kisan Gold", tenant_id=tenant_id)
    update = BrandUpdate(tenant_id=tenant_id)
    assert create.tenant_id == tenant_id
    assert update.tenant_id == tenant_id


def test_brand_write_tenant_id_must_match_authenticated_tenant():
    tenant_id = uuid.uuid4()
    other_tenant_id = uuid.uuid4()
    user = CurrentUser(user_id=uuid.uuid4(), tenant_id=tenant_id, role="OWNER")

    assert _resolve_brand_tenant(user, None, tenant_id) == tenant_id
    with pytest.raises(HTTPException) as error:
        _resolve_brand_tenant(user, None, other_tenant_id)
    assert error.value.status_code == 403
