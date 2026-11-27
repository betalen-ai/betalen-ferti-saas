from app.models.ferti import Brand


def test_brand_model_matches_shop_brand_fields_and_is_tenant_scoped():
    assert set(Brand.__table__.columns.keys()) >= {
        "id",
        "tenant_id",
        "name",
        "manufacturer",
        "notes",
        "active",
        "created_at",
        "updated_at",
        "version",
    }
