import uuid
import hashlib
import hmac
import secrets
import urllib.parse
from io import BytesIO
from functools import partial
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy import Date, Numeric, case, delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.postgresql import insert

from app.config import settings
from app.db import get_db
from app.models import (
    AuthActionToken,
    AuthIdentity,
    AuthRateLimit,
    AuditLog,
    Bill,
    BillDraft,
    BillItem,
    Brand,
    CashbookEntry,
    Category,
    Farmer,
    IdempotencyRecord,
    KhataEntry,
    OrgUser,
    OtpChallenge,
    Pack,
    Payment,
    PaymentAllocation,
    Product,
    RefreshSession,
    Season,
    Setting,
    StockLot,
    StockMovement,
    Tenant,
)
from app.schemas.auth import LoginRequest
from app.schemas.tenant import TenantOut, TenantSignupRequest
from app.services.auth_service import authenticate_user, create_access_token, hash_password, verify_password
from app.services.tenant_service import signup_tenant

router = APIRouter(prefix="/api/v1")
bearer_scheme = HTTPBearer(auto_error=False)

RESOURCES = {
    "brands": Brand,
    "categories": Category,
    "products": Product,
    "packs": Pack,
    "farmers": Farmer,
    "seasons": Season,
    "cashbook": CashbookEntry,
}
ZERO = Decimal("0.00")
CENT = Decimal("0.01")


async def current_identity(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, uuid.UUID]:
    token = credentials.credentials if credentials else request.cookies.get("access_token")
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="authentication_required")
    if credentials is None and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        _validate_cookie_csrf(request)
    try:
        claims = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return {"user_id": uuid.UUID(claims["sub"]), "tenant_id": uuid.UUID(claims["tid"])}
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_session") from exc


def _wire(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (uuid.UUID, date, datetime)):
        return value.isoformat() if isinstance(value, (date, datetime)) else str(value)
    if isinstance(value, dict):
        return {key: _wire(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_wire(item) for item in value]
    return value


def _row(model: Any, include: set[str] | None = None) -> dict[str, Any]:
    return {
        column.name: _wire(getattr(model, column.name))
        for column in model.__table__.columns
        if include is None or column.name in include
    }


def _decimal(value: Any, field: str, *, minimum: Decimal | None = None) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise HTTPException(422, detail=f"{field} must be a decimal value") from exc
    if not result.is_finite() or (minimum is not None and result < minimum):
        raise HTTPException(422, detail=f"{field} is outside the permitted range")
    return result


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _pdf_response(title: str, lines: list[str], filename: str) -> Response:
    def escape(value: str) -> str:
        return value.encode("latin-1", "replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content = ["BT", "/F1 14 Tf", "50 790 Td", f"({escape(title)}) Tj", "/F1 10 Tf"]
    for line in lines:
        content.extend(["0 -18 Td", f"({escape(line)}) Tj"])
    content.append("ET")
    stream = "\n".join(content).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii") + obj + b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return Response(
        content=bytes(output),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _xlsx_response(title: str, columns: list[str], rows: list[list[Any]], filename: str) -> Response:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = title[:31]
    sheet.append(columns)
    for row in rows:
        sheet.append([_wire(value) for value in row])
    stream = BytesIO()
    workbook.save(stream)
    return Response(
        content=stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _export_response(
    format: str | None,
    title: str,
    columns: list[str],
    rows: list[list[Any]],
    filename: str,
) -> Response | None:
    if format is None:
        return None
    if format == "xlsx":
        return _xlsx_response(title, columns, rows, f"{filename}.xlsx")
    if format == "pdf":
        lines = [" | ".join(columns)]
        lines.extend(" | ".join(str(_wire(value) or "") for value in row) for row in rows)
        return _pdf_response(title, lines, f"{filename}.pdf")
    raise HTTPException(422, detail="format must be pdf or xlsx")


def _secret_hash(value: str) -> str:
    return hmac.new(settings.JWT_SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()


async def _enforce_auth_rate_limit(
    db: AsyncSession,
    request: Request,
    *,
    action: str,
    subject: str,
    limit: int,
    window_seconds: int,
) -> None:
    now = datetime.now(timezone.utc)
    window_epoch = int(now.timestamp()) // window_seconds * window_seconds
    window_start = datetime.fromtimestamp(window_epoch, timezone.utc)
    peer = request.client.host if request.client else "unknown"
    subject_hash = _secret_hash(f"{action}:{peer}:{subject.lower()}")
    await db.execute(delete(AuthRateLimit).where(
        AuthRateLimit.window_start < now - timedelta(days=1)
    ))
    statement = insert(AuthRateLimit).values(
        action=action,
        subject_hash=subject_hash,
        window_start=window_start,
        count=1,
    ).on_conflict_do_update(
        index_elements=["action", "subject_hash", "window_start"],
        set_={"count": AuthRateLimit.count + 1},
    ).returning(AuthRateLimit.count)
    count = await db.scalar(statement)
    await db.commit()
    if count and count > limit:
        raise HTTPException(429, detail="rate_limit_exceeded", headers={"Retry-After": str(window_seconds)})


async def _send_provider_message(
    url: str | None,
    api_key: str | None,
    payload: dict[str, str],
    *,
    integration: str,
) -> None:
    if not url:
        raise HTTPException(503, detail=f"{integration}_provider_not_configured")
    if settings.ENVIRONMENT.lower() == "production" and urllib.parse.urlparse(url).scheme != "https":
        raise HTTPException(503, detail=f"{integration}_provider_requires_https")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(502, detail=f"{integration}_delivery_failed") from exc


async def _issue_session(db: AsyncSession, user: OrgUser) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    refresh_token = secrets.token_urlsafe(48)
    db.add(RefreshSession(
        tenant_id=user.tenant_id,
        user_id=user.id,
        token_hash=_secret_hash(refresh_token),
        expires_at=now + timedelta(days=30),
    ))
    await db.flush()
    return {
        "access_token": create_access_token(user_id=user.id, tenant_id=user.tenant_id, email=user.email),
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
    }


def _set_session_cookies(response: Response, tokens: dict[str, Any]) -> None:
    secure = settings.ENVIRONMENT.lower() == "production"
    response.set_cookie(
        "access_token", tokens["access_token"], httponly=True, secure=secure,
        samesite="lax", max_age=settings.JWT_EXPIRE_MINUTES * 60, path="/",
    )
    response.set_cookie(
        "refresh_token", tokens["refresh_token"], httponly=True, secure=secure,
        samesite="lax", max_age=30 * 24 * 60 * 60, path="/api/v1/auth",
    )
    response.set_cookie(
        "csrf_token", secrets.token_urlsafe(32), httponly=False, secure=secure,
        samesite="lax", max_age=30 * 24 * 60 * 60, path="/",
    )


def _validate_cookie_csrf(request: Request) -> None:
    if request.cookies.get("access_token") or request.cookies.get("refresh_token"):
        cookie_token = request.cookies.get("csrf_token", "")
        header_token = request.headers.get("x-csrf-token", "")
        if not cookie_token or not hmac.compare_digest(cookie_token, header_token):
            raise HTTPException(403, detail="csrf_validation_failed")


async def _new_action_token(
    db: AsyncSession,
    user: OrgUser,
    *,
    purpose: str,
    lifetime: timedelta,
) -> str:
    token = secrets.token_urlsafe(40)
    db.add(AuthActionToken(
        tenant_id=user.tenant_id,
        user_id=user.id,
        purpose=purpose,
        token_hash=_secret_hash(token),
        expires_at=datetime.now(timezone.utc) + lifetime,
    ))
    return token


async def _owned(
    db: AsyncSession,
    model: Any,
    tenant_id: uuid.UUID,
    record_id: uuid.UUID,
    *,
    lock: bool = False,
) -> Any:
    statement = select(model).where(model.id == record_id, model.tenant_id == tenant_id)
    if lock:
        statement = statement.with_for_update()
    item = (await db.execute(statement)).scalar_one_or_none()
    if item is None:
        raise HTTPException(404, detail="record_not_found")
    return item


async def _audit(
    db: AsyncSession,
    identity: dict[str, uuid.UUID],
    entity: str,
    entity_id: uuid.UUID,
    action: str,
    old: dict[str, Any] | None,
    new: dict[str, Any] | None,
) -> None:
    db.add(AuditLog(
        tenant_id=identity["tenant_id"],
        user_id=identity["user_id"],
        entity_type=entity,
        entity_id=entity_id,
        action=action,
        old_values=old,
        new_values=new,
    ))


def _pack_factor(product: Product, size: Any, unit_value: str) -> Decimal:
    unit = str(unit_value).lower()
    factors = {"g": Decimal("0.001"), "kg": Decimal("1"), "ml": Decimal("0.001"), "l": Decimal("1"), "piece": Decimal("1")}
    valid_units = {"solid": {"g", "kg"}, "liquid": {"ml", "l"}, "item": {"piece"}}
    if unit not in valid_units[product.unit_type]:
        raise HTTPException(422, detail="size_unit does not match product type")
    return _decimal(size, "size", minimum=Decimal("0.001")) * factors[unit]


def _payload_values(model: Any, payload: dict[str, Any], tenant_id: uuid.UUID) -> dict[str, Any]:
    allowed = {column.name for column in model.__table__.columns} - {
        "id", "tenant_id", "created_at", "updated_at", "version"
    }
    unknown = set(payload) - allowed
    if model is Pack and "size_in_base_unit" in payload:
        unknown.add("size_in_base_unit")
    if unknown:
        raise HTTPException(422, detail=f"Unknown fields: {', '.join(sorted(unknown))}")
    values = dict(payload)
    for column in model.__table__.columns:
        key = column.name
        if key not in values or values[key] is None:
            continue
        try:
            if isinstance(column.type, PG_UUID):
                values[key] = uuid.UUID(str(values[key]))
            elif isinstance(column.type, Numeric):
                values[key] = Decimal(str(values[key]))
            elif isinstance(column.type, Date) and isinstance(values[key], str):
                values[key] = date.fromisoformat(values[key])
        except (ValueError, InvalidOperation) as exc:
            raise HTTPException(422, detail=f"Invalid value for {key}") from exc
    values["tenant_id"] = tenant_id
    return values


async def list_resource(
    resource: str,
    q: str | None = None,
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=100),
    sort: str | None = None,
    brandId: uuid.UUID | None = None,
    categoryId: uuid.UUID | None = None,
    active: bool | None = None,
    village: str | None = None,
    hasDues: bool | None = None,
    overdue: bool | None = None,
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    model = RESOURCES.get(resource)
    if model is None:
        raise HTTPException(404, detail="resource_not_found")
    statement = select(model).where(model.tenant_id == identity["tenant_id"])
    if brandId:
        if model is not Product:
            raise HTTPException(422, detail="brandId filter is only supported for products")
        statement = statement.where(Product.brand_id == brandId)
    if categoryId:
        if model is not Product:
            raise HTTPException(422, detail="categoryId filter is only supported for products")
        statement = statement.where(Product.category_id == categoryId)
    if active is not None:
        if not hasattr(model, "active"):
            raise HTTPException(422, detail="active filter is not supported for this resource")
        statement = statement.where(model.active.is_(active))
    if village:
        if model is not Farmer:
            raise HTTPException(422, detail="village filter is only supported for farmers")
        statement = statement.where(Farmer.village.ilike(f"%{village}%"))
    if hasDues is not None or overdue:
        if model is not Farmer:
            raise HTTPException(422, detail="dues filters are only supported for farmers")
        due_query = select(Bill.farmer_id).where(
            Bill.tenant_id == identity["tenant_id"], Bill.status == "posted", Bill.balance > 0
        )
        if overdue:
            due_query = due_query.where(Bill.due_date < date.today())
        statement = statement.where(model.id.in_(due_query) if hasDues or overdue else model.id.not_in(due_query))
    if q:
        search_columns = [column for column in model.__table__.columns if str(column.type).upper().startswith("VARCHAR") or str(column.type).upper() == "TEXT"]
        if search_columns:
            statement = statement.where(or_(*(column.ilike(f"%{q}%") for column in search_columns)))
    if sort:
        field, separator, direction = sort.partition(":")
        if not separator or field not in model.__table__.columns or direction not in {"asc", "desc"}:
            raise HTTPException(422, detail="sort must use field:asc or field:desc")
        sort_column = getattr(model, field)
        statement = statement.order_by(sort_column.asc() if direction == "asc" else sort_column.desc())
    total = await db.scalar(select(func.count()).select_from(statement.order_by(None).subquery()))
    records = (await db.execute(statement.offset((page - 1) * pageSize).limit(pageSize))).scalars().all()
    items = [_row(record) for record in records]
    if resource == "brands":
        counts = dict((await db.execute(
            select(Product.brand_id, func.count()).where(
                Product.tenant_id == identity["tenant_id"],
                Product.brand_id.in_([record.id for record in records]),
            ).group_by(Product.brand_id)
        )).all())
        for item, record in zip(items, records):
            item["productCount"] = counts.get(record.id, 0)
    if resource == "products":
        packs = (await db.execute(select(Pack).where(
            Pack.tenant_id == identity["tenant_id"],
            Pack.product_id.in_([record.id for record in records]),
            Pack.active.is_(True),
        ))).scalars().all()
        stock = dict((await db.execute(
            select(StockMovement.pack_id, func.coalesce(func.sum(StockMovement.quantity_base), 0))
            .where(
                StockMovement.tenant_id == identity["tenant_id"],
                StockMovement.pack_id.in_([pack.id for pack in packs]),
            )
            .group_by(StockMovement.pack_id)
        )).all()) if packs else {}
        packs_by_product: dict[uuid.UUID, list[Pack]] = {}
        for pack in packs:
            packs_by_product.setdefault(pack.product_id, []).append(pack)
        for item, record in zip(items, records):
            product_packs = packs_by_product.get(record.id, [])
            item["packs"] = [_row(pack) for pack in product_packs]
            item["stockByPack"] = {str(pack.id): str(stock.get(pack.id, 0)) for pack in product_packs}
    return {"items": items, "page": page, "pageSize": pageSize, "total": total or 0}


async def create_resource(
    resource: str,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    model = RESOURCES.get(resource)
    if model is None:
        raise HTTPException(404, detail="resource_not_found")
    values = _payload_values(model, payload, identity["tenant_id"])
    if model is Product:
        for field, referenced_model in (("brand_id", Brand), ("category_id", Category)):
            if values.get(field):
                await _owned(db, referenced_model, identity["tenant_id"], uuid.UUID(str(values[field])))
    if model is Product and values.get("unit_type") not in {"solid", "liquid", "item"}:
        raise HTTPException(422, detail="unit_type must be solid, liquid, or item")
    if model is Category and values.get("product_type") not in {"solid", "liquid", "item"}:
        raise HTTPException(422, detail="product_type must be solid, liquid, or item")
    if model is CashbookEntry:
        if values.get("direction") not in {"in", "out"}:
            raise HTTPException(422, detail="direction must be in or out")
        if values.get("amount", ZERO) <= ZERO:
            raise HTTPException(422, detail="amount must be greater than zero")
    if model is Season:
        if values.get("start_date") is None or values.get("end_date") is None:
            raise HTTPException(422, detail="start_date and end_date are required")
        if values["end_date"] < values["start_date"]:
            raise HTTPException(422, detail="end_date must not be before start_date")
    if model is Pack:
        if not values.get("product_id") or "size" not in values or "size_unit" not in values:
            raise HTTPException(422, detail="product_id, size, and size_unit are required")
        product = await _owned(db, Product, identity["tenant_id"], uuid.UUID(str(values["product_id"])))
        values["size_in_base_unit"] = _pack_factor(product, values["size"], values["size_unit"])
    record = model(**values)
    db.add(record)
    try:
        await db.flush()
        if model is Farmer and record.opening_balance:
            db.add(KhataEntry(
                tenant_id=identity["tenant_id"],
                farmer_id=record.id,
                entry_type="opening_balance",
                debit=record.opening_balance,
                credit=ZERO,
                description="Opening balance",
            ))
        entity_names = {"brands": "brand", "categories": "category", "products": "product", "packs": "pack", "farmers": "farmer", "seasons": "season", "cashbook": "cashbook"}
        await _audit(db, identity, entity_names[resource], record.id, "create", None, _row(record))
        await db.commit()
        await db.refresh(record)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, detail="record_conflict") from exc
    return _row(record)


@router.get("/packs/lookup")
async def lookup_pack(
    barcode: str,
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    pack = (await db.execute(select(Pack).where(
        Pack.tenant_id == identity["tenant_id"], Pack.barcode == barcode, Pack.active.is_(True)
    ))).scalar_one_or_none()
    if pack is None:
        raise HTTPException(404, detail="pack_not_found")
    result = _row(pack)
    result["stockBase"] = str(await db.scalar(select(func.coalesce(func.sum(StockMovement.quantity_base), 0)).where(
        StockMovement.tenant_id == identity["tenant_id"], StockMovement.pack_id == pack.id
    )))
    return result


@router.post("/products/{product_id:uuid}/packs", status_code=status.HTTP_201_CREATED)
async def add_product_pack(
    product_id: uuid.UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    await _owned(db, Product, identity["tenant_id"], product_id)
    return await create_resource("packs", {**payload, "product_id": str(product_id)}, db, identity)


async def get_resource(
    resource: str,
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    model = RESOURCES.get(resource)
    if model is None:
        raise HTTPException(404, detail="resource_not_found")
    return _row(await _owned(db, model, identity["tenant_id"], record_id))


async def patch_resource(
    resource: str,
    record_id: uuid.UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    model = RESOURCES.get(resource)
    if model is None:
        raise HTTPException(404, detail="resource_not_found")
    if "version" not in payload:
        raise HTTPException(422, detail="version is required for updates")
    record = await _owned(db, model, identity["tenant_id"], record_id, lock=True)
    if payload["version"] != record.version:
        raise HTTPException(409, detail="record_version_conflict")
    old = _row(record)
    values = _payload_values(model, {key: value for key, value in payload.items() if key != "version"}, identity["tenant_id"])
    values.pop("tenant_id", None)
    if model is Product and values.get("unit_type") not in {None, "solid", "liquid", "item"}:
        raise HTTPException(422, detail="unit_type must be solid, liquid, or item")
    if model is Category and values.get("product_type") not in {None, "solid", "liquid", "item"}:
        raise HTTPException(422, detail="product_type must be solid, liquid, or item")
    if model is CashbookEntry:
        if values.get("direction", record.direction) not in {"in", "out"}:
            raise HTTPException(422, detail="direction must be in or out")
        if values.get("amount", record.amount) <= ZERO:
            raise HTTPException(422, detail="amount must be greater than zero")
    if model is Season and values.get("end_date", record.end_date) < values.get("start_date", record.start_date):
        raise HTTPException(422, detail="end_date must not be before start_date")
    if model is Pack and ({"size", "size_unit", "product_id"} & set(values)):
        pack_product = await _owned(
            db, Product, identity["tenant_id"], uuid.UUID(str(values.get("product_id", record.product_id)))
        )
        values["size_in_base_unit"] = _pack_factor(
            pack_product,
            values.get("size", record.size),
            values.get("size_unit", record.size_unit).lower(),
        )
    if model is Product:
        for field, referenced_model in (("brand_id", Brand), ("category_id", Category)):
            if values.get(field):
                await _owned(db, referenced_model, identity["tenant_id"], uuid.UUID(str(values[field])))
    for key, value in values.items():
        setattr(record, key, value)
    record.version += 1
    try:
        entity_names = {"brands": "brand", "categories": "category", "products": "product", "packs": "pack", "farmers": "farmer", "seasons": "season", "cashbook": "cashbook"}
        await _audit(db, identity, entity_names[resource], record.id, "update", old, _row(record))
        await db.commit()
        await db.refresh(record)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, detail="record_conflict") from exc
    return _row(record)


for resource_name in RESOURCES:
    router.add_api_route(
        f"/{resource_name}",
        partial(list_resource, resource_name),
        methods=["GET"],
        name=f"list_{resource_name}",
    )
    router.add_api_route(
        f"/{resource_name}",
        partial(create_resource, resource_name),
        methods=["POST"],
        status_code=status.HTTP_201_CREATED,
        name=f"create_{resource_name}",
    )
    router.add_api_route(
        f"/{resource_name}/{{record_id:uuid}}",
        partial(get_resource, resource_name),
        methods=["GET"],
        name=f"get_{resource_name}",
    )
    router.add_api_route(
        f"/{resource_name}/{{record_id:uuid}}",
        partial(patch_resource, resource_name),
        methods=["PATCH"],
        name=f"patch_{resource_name}",
    )


@router.get("/tenant/me")
async def tenant_me(db: AsyncSession = Depends(get_db), identity: dict[str, uuid.UUID] = Depends(current_identity)):
    tenant = (await db.execute(select(Tenant).where(Tenant.id == identity["tenant_id"]))).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(404, detail="tenant_not_found")
    return _row(tenant)


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register_owner(
    payload: TenantSignupRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await _enforce_auth_rate_limit(
        db, request, action="register", subject=str(payload.owner_email), limit=5, window_seconds=3600
    )
    if not settings.EMAIL_PROVIDER_URL:
        raise HTTPException(503, detail="email_provider_not_configured")
    tenant = await signup_tenant(db, payload)
    owner = (await db.execute(select(OrgUser).where(
        OrgUser.tenant_id == tenant.id, OrgUser.email == str(payload.owner_email)
    ))).scalar_one()
    owner.email_verified = False
    verify_token = await _new_action_token(
        db, owner, purpose="email_verification", lifetime=timedelta(hours=24)
    )
    await db.commit()
    verification_link = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={verify_token}"
    await _send_provider_message(
        settings.EMAIL_PROVIDER_URL,
        settings.EMAIL_PROVIDER_API_KEY,
        {
            "to": owner.email,
            "subject": "Verify your Ferti+ account",
            "text": f"Verify your email using this single-use token: {verify_token}\n{verification_link}",
        },
        integration="email",
    )
    response.status_code = status.HTTP_201_CREATED
    return {"tenant": TenantOut.model_validate(tenant), "emailVerificationRequired": True}


@router.post("/auth/login")
async def login_owner(
    payload: LoginRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await _enforce_auth_rate_limit(
        db, request, action="login", subject=f"{payload.subdomain}:{payload.email}", limit=5, window_seconds=60
    )
    tenant = (await db.execute(select(Tenant).where(Tenant.subdomain == payload.subdomain))).scalar_one_or_none()
    if tenant is None or tenant.status != "active":
        raise HTTPException(401, detail="invalid_credentials")
    user = await authenticate_user(
        db, tenant_id=tenant.id, email=str(payload.email), password=payload.password
    )
    if user is None:
        raise HTTPException(401, detail="invalid_credentials")
    if not user.email_verified:
        raise HTTPException(403, detail="email_verification_required")
    tokens = await _issue_session(db, user)
    await db.commit()
    _set_session_cookies(response, tokens)
    return tokens


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    request: Request,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
):
    _validate_cookie_csrf(request)
    refresh_token = (payload or {}).get("refreshToken") or request.cookies.get("refresh_token")
    if refresh_token:
        session = (await db.execute(select(RefreshSession).where(
            RefreshSession.token_hash == _secret_hash(str(refresh_token)),
            RefreshSession.revoked_at.is_(None),
        ).with_for_update())).scalar_one_or_none()
        if session:
            session.revoked_at = datetime.now(timezone.utc)
            await db.commit()
    secure = settings.ENVIRONMENT.lower() == "production"
    response.delete_cookie("access_token", httponly=True, secure=secure, samesite="lax", path="/")
    response.delete_cookie("refresh_token", httponly=True, secure=secure, samesite="lax", path="/api/v1/auth")
    response.delete_cookie("csrf_token", httponly=False, secure=secure, samesite="lax", path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/auth/otp/send", status_code=status.HTTP_202_ACCEPTED)
async def send_otp(
    payload: dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    phone = str(payload.get("phone", "")).strip()
    purpose = str(payload.get("purpose", "")).lower()
    subdomain = str(payload["subdomain"]).lower() if payload.get("subdomain") else None
    if not phone or purpose not in {"sign_in", "sign_up", "reset"}:
        raise HTTPException(422, detail="phone and a supported purpose are required")
    if purpose != "sign_up" and not subdomain:
        raise HTTPException(422, detail="subdomain is required for sign-in and reset")
    await _enforce_auth_rate_limit(
        db, request, action="otp_send", subject=f"{phone}:{purpose}", limit=5, window_seconds=900
    )
    latest = (await db.execute(select(OtpChallenge).where(
        OtpChallenge.phone == phone,
        OtpChallenge.purpose == purpose,
        OtpChallenge.subdomain == subdomain,
    ).order_by(OtpChallenge.created_at.desc()).limit(1))).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if latest and (now - latest.created_at).total_seconds() < 30:
        raise HTTPException(429, detail="otp_resend_cooldown", headers={"Retry-After": "30"})
    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = OtpChallenge(
        phone=phone,
        subdomain=subdomain,
        purpose=purpose,
        code_hash=_secret_hash(f"{phone}:{purpose}:{subdomain or ''}:{code}"),
        attempts=0,
        expires_at=now + timedelta(minutes=5),
    )
    db.add(challenge)
    await _send_provider_message(
        settings.OTP_PROVIDER_URL,
        settings.OTP_PROVIDER_API_KEY,
        {"to": phone, "message": f"Your Ferti+ verification code is {code}. It expires in 5 minutes."},
        integration="otp",
    )
    await db.commit()
    return {"status": "sent", "expiresIn": 300, "resendAfter": 30}


@router.post("/auth/otp/verify")
async def verify_otp(
    payload: dict[str, Any],
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    phone = str(payload.get("phone", "")).strip()
    purpose = str(payload.get("purpose", "")).lower()
    subdomain = str(payload["subdomain"]).lower() if payload.get("subdomain") else None
    code = str(payload.get("code", ""))
    if not phone or purpose not in {"sign_in", "sign_up", "reset"} or len(code) != 6 or not code.isdigit():
        raise HTTPException(422, detail="phone, purpose, and six-digit code are required")
    await _enforce_auth_rate_limit(
        db, request, action="otp_verify", subject=f"{phone}:{purpose}", limit=10, window_seconds=900
    )
    challenge = (await db.execute(select(OtpChallenge).where(
        OtpChallenge.phone == phone,
        OtpChallenge.purpose == purpose,
        OtpChallenge.subdomain == subdomain,
    ).order_by(OtpChallenge.created_at.desc()).limit(1).with_for_update())).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if not challenge or challenge.consumed_at or challenge.expires_at <= now or challenge.attempts >= 5:
        raise HTTPException(401, detail="invalid_or_expired_otp")
    challenge.attempts += 1
    expected_hash = _secret_hash(f"{phone}:{purpose}:{subdomain or ''}:{code}")
    if not hmac.compare_digest(challenge.code_hash, expected_hash):
        await db.commit()
        raise HTTPException(401, detail="invalid_or_expired_otp")
    challenge.consumed_at = now
    if purpose == "sign_up":
        registration = payload.get("registration")
        if not isinstance(registration, dict):
            raise HTTPException(422, detail="registration details are required after OTP verification")
        registration_payload = TenantSignupRequest.model_validate(registration)
        if registration_payload.owner_phone and registration_payload.owner_phone != phone:
            raise HTTPException(422, detail="registration phone must match the verified phone")
        registration_payload.owner_phone = phone
        tenant = await signup_tenant(db, registration_payload)
        user = (await db.execute(select(OrgUser).where(
            OrgUser.tenant_id == tenant.id, OrgUser.phone == phone
        ))).scalar_one()
        tokens = await _issue_session(db, user)
        await db.commit()
        _set_session_cookies(response, tokens)
        return {"tenant": TenantOut.model_validate(tenant), **tokens}
    tenant = (await db.execute(select(Tenant).where(Tenant.subdomain == subdomain))).scalar_one_or_none()
    user = None
    if tenant and tenant.status == "active":
        user = (await db.execute(select(OrgUser).where(
            OrgUser.tenant_id == tenant.id, OrgUser.phone == phone, OrgUser.status == "active"
        ))).scalar_one_or_none()
    if purpose == "sign_in":
        if user is None:
            raise HTTPException(401, detail="invalid_or_expired_otp")
        tokens = await _issue_session(db, user)
        await db.commit()
        _set_session_cookies(response, tokens)
        return tokens
    if user is None:
        await db.commit()
        return {"status": "verified"}
    reset_token = await _new_action_token(db, user, purpose="password_reset", lifetime=timedelta(minutes=30))
    await db.commit()
    return {"status": "verified", "resetToken": reset_token, "expiresIn": 1800}


@router.post("/auth/verify-email")
async def verify_email(payload: dict[str, Any], db: AsyncSession = Depends(get_db)):
    token = str(payload.get("token", ""))
    if not token:
        raise HTTPException(422, detail="token is required")
    action = (await db.execute(select(AuthActionToken).where(
        AuthActionToken.token_hash == _secret_hash(token),
        AuthActionToken.purpose == "email_verification",
    ).with_for_update())).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if not action or action.consumed_at or action.expires_at <= now:
        raise HTTPException(400, detail="invalid_or_expired_verification_token")
    user = (await db.execute(select(OrgUser).where(
        OrgUser.id == action.user_id, OrgUser.tenant_id == action.tenant_id
    ))).scalar_one_or_none()
    if not user:
        raise HTTPException(400, detail="invalid_or_expired_verification_token")
    action.consumed_at = now
    user.email_verified = True
    await db.commit()
    return {"status": "verified"}


@router.post("/auth/verify-email/send", status_code=status.HTTP_202_ACCEPTED)
async def send_verification_email(
    payload: dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    email = str(payload.get("email", "")).strip().lower()
    subdomain = str(payload.get("subdomain", "")).strip().lower()
    if not email or not subdomain:
        raise HTTPException(422, detail="email and subdomain are required")
    await _enforce_auth_rate_limit(db, request, action="verify_email", subject=f"{email}:{subdomain}", limit=3, window_seconds=3600)
    if not settings.EMAIL_PROVIDER_URL:
        raise HTTPException(503, detail="email_provider_not_configured")
    user = (await db.execute(
        select(OrgUser).join(Tenant, Tenant.id == OrgUser.tenant_id).where(
            Tenant.subdomain == subdomain, OrgUser.email == email, OrgUser.email_verified.is_(False)
        )
    )).scalar_one_or_none()
    if user:
        token = await _new_action_token(db, user, purpose="email_verification", lifetime=timedelta(hours=24))
        await db.commit()
        text = f"Verify your Ferti+ account with this single-use token: {token}"
    else:
        text = "If the account needs verification, follow the verification instructions previously sent."
    await _send_provider_message(
        settings.EMAIL_PROVIDER_URL, settings.EMAIL_PROVIDER_API_KEY,
        {"to": email, "subject": "Ferti+ email verification", "text": text},
        integration="email",
    )
    return {"status": "accepted"}


@router.post("/auth/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    payload: dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    email = str(payload.get("email", "")).strip().lower()
    subdomain = str(payload.get("subdomain", "")).strip().lower()
    if not email or not subdomain:
        raise HTTPException(422, detail="email and subdomain are required")
    await _enforce_auth_rate_limit(db, request, action="forgot_password", subject=f"{email}:{subdomain}", limit=5, window_seconds=3600)
    if not settings.EMAIL_PROVIDER_URL:
        raise HTTPException(503, detail="email_provider_not_configured")
    user = (await db.execute(
        select(OrgUser).join(Tenant, Tenant.id == OrgUser.tenant_id).where(
            Tenant.subdomain == subdomain, OrgUser.email == email
        )
    )).scalar_one_or_none()
    text = "If an account exists for these details, a password reset token will be sent."
    if user:
        token = await _new_action_token(db, user, purpose="password_reset", lifetime=timedelta(minutes=30))
        await db.commit()
        text += f"\nSingle-use reset token: {token}"
    await _send_provider_message(
        settings.EMAIL_PROVIDER_URL, settings.EMAIL_PROVIDER_API_KEY,
        {"to": email, "subject": "Ferti+ password reset", "text": text},
        integration="email",
    )
    return {"status": "accepted"}


@router.post("/auth/reset-password")
async def reset_password(
    payload: dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    token = str(payload.get("token", ""))
    password = payload.get("newPassword")
    if not token or not isinstance(password, str) or len(password) < 8 or len(password) > 128:
        raise HTTPException(422, detail="token and a password of 8 to 128 characters are required")
    await _enforce_auth_rate_limit(db, request, action="reset_password", subject=token, limit=5, window_seconds=3600)
    action = (await db.execute(select(AuthActionToken).where(
        AuthActionToken.token_hash == _secret_hash(token),
        AuthActionToken.purpose == "password_reset",
    ).with_for_update())).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if not action or action.consumed_at or action.expires_at <= now:
        raise HTTPException(400, detail="invalid_or_expired_reset_token")
    user = (await db.execute(select(OrgUser).where(
        OrgUser.id == action.user_id, OrgUser.tenant_id == action.tenant_id
    ).with_for_update())).scalar_one_or_none()
    if not user:
        raise HTTPException(400, detail="invalid_or_expired_reset_token")
    action.consumed_at = now
    user.password_hash = hash_password(password)
    sessions = (await db.execute(select(RefreshSession).where(
        RefreshSession.tenant_id == action.tenant_id,
        RefreshSession.user_id == user.id,
        RefreshSession.revoked_at.is_(None),
    ).with_for_update())).scalars().all()
    for session in sessions:
        session.revoked_at = now
    await db.commit()
    return {"status": "password_updated"}


@router.post("/auth/refresh")
async def refresh_session(
    request: Request,
    response: Response,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
):
    _validate_cookie_csrf(request)
    refresh_token = (payload or {}).get("refreshToken") or request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(401, detail="refresh_token_required")
    await _enforce_auth_rate_limit(db, request, action="refresh", subject=str(refresh_token), limit=20, window_seconds=3600)
    session = (await db.execute(select(RefreshSession).where(
        RefreshSession.token_hash == _secret_hash(str(refresh_token)),
        RefreshSession.revoked_at.is_(None),
    ).with_for_update())).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if not session or session.expires_at <= now:
        raise HTTPException(401, detail="invalid_or_expired_refresh_token")
    user = (await db.execute(select(OrgUser).where(
        OrgUser.id == session.user_id, OrgUser.tenant_id == session.tenant_id
    ))).scalar_one_or_none()
    tenant = (await db.execute(select(Tenant).where(Tenant.id == session.tenant_id))).scalar_one_or_none()
    if not user or not tenant or user.status != "active" or tenant.status != "active":
        raise HTTPException(401, detail="invalid_or_expired_refresh_token")
    session.revoked_at = now
    tokens = await _issue_session(db, user)
    await db.commit()
    _set_session_cookies(response, tokens)
    return tokens


@router.get("/auth/oauth/google")
async def google_oauth_start(request: Request, db: AsyncSession = Depends(get_db)):
    await _enforce_auth_rate_limit(db, request, action="google_oauth", subject="start", limit=20, window_seconds=60)
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(503, detail="google_oauth_not_configured")
    nonce = secrets.token_urlsafe(24)
    state = jwt.encode(
        {"purpose": "google_oauth_state", "nonce": nonce, "exp": datetime.now(timezone.utc) + timedelta(minutes=10)},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
    }
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}")


@router.get("/auth/oauth/google/callback")
async def google_oauth_callback(
    code: str,
    state: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(503, detail="google_oauth_not_configured")
    try:
        state_claims = jwt.decode(state, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(401, detail="invalid_oauth_state") from exc
    if state_claims.get("purpose") != "google_oauth_state":
        raise HTTPException(401, detail="invalid_oauth_state")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            exchange = await client.post("https://oauth2.googleapis.com/token", data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            })
            exchange.raise_for_status()
            id_token = exchange.json()["id_token"]
            verified = await client.get("https://oauth2.googleapis.com/tokeninfo", params={"id_token": id_token})
            verified.raise_for_status()
            claims = verified.json()
    except (httpx.HTTPError, KeyError) as exc:
        raise HTTPException(401, detail="google_authentication_failed") from exc
    if (
        claims.get("aud") != settings.GOOGLE_CLIENT_ID
        or claims.get("nonce") != state_claims.get("nonce")
        or claims.get("email_verified") not in {True, "true"}
        or not claims.get("sub")
        or not claims.get("email")
    ):
        raise HTTPException(401, detail="google_authentication_failed")
    identity = (await db.execute(select(AuthIdentity).where(
        AuthIdentity.provider == "google", AuthIdentity.provider_subject == claims["sub"]
    ))).scalar_one_or_none()
    if identity:
        user = (await db.execute(select(OrgUser).where(
            OrgUser.id == identity.user_id, OrgUser.tenant_id == identity.tenant_id,
            OrgUser.status == "active",
        ))).scalar_one_or_none()
    else:
        users = (await db.execute(select(OrgUser).where(
            OrgUser.email == claims["email"].lower(), OrgUser.status == "active"
        ))).scalars().all()
        if len(users) != 1:
            raise HTTPException(409, detail="google_account_not_linked_or_ambiguous")
        user = users[0]
        if not user.email_verified:
            raise HTTPException(403, detail="email_verification_required")
        db.add(AuthIdentity(
            tenant_id=user.tenant_id, user_id=user.id,
            provider="google", provider_subject=claims["sub"],
        ))
    if not user:
        raise HTTPException(401, detail="google_account_not_linked")
    tokens = await _issue_session(db, user)
    await db.commit()
    _set_session_cookies(response, tokens)
    return tokens


@router.patch("/tenant/me")
async def update_tenant(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    allowed = {"name", "address", "gstin", "phone", "logo_url"}
    if set(payload) - allowed:
        raise HTTPException(422, detail="Only shop profile fields may be updated")
    tenant = (await db.execute(select(Tenant).where(Tenant.id == identity["tenant_id"]).with_for_update())).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(404, detail="tenant_not_found")
    old = {key: getattr(tenant, key) for key in allowed}
    for key, value in payload.items():
        setattr(tenant, key, value)
    await _audit(db, identity, "tenant", tenant.id, "update", old, {key: getattr(tenant, key) for key in allowed})
    await db.commit()
    return _row(tenant)


@router.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db), identity: dict[str, uuid.UUID] = Depends(current_identity)):
    row = await db.get(Setting, identity["tenant_id"])
    return row.values if row else {}


@router.put("/settings")
async def put_settings(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    allowed = {"taxMode", "defaultGstByCategory", "billNumberPrefix", "invoiceFooter", "defaultInterest", "defaultDiscount", "rounding"}
    if set(payload) - allowed:
        raise HTTPException(422, detail="Unknown setting")
    row = await db.get(Setting, identity["tenant_id"], with_for_update=True)
    old_values = row.values if row else None
    if row is None:
        row = Setting(tenant_id=identity["tenant_id"], values=payload)
        db.add(row)
    else:
        row.values = payload
    await _audit(db, identity, "setting", identity["tenant_id"], "update", old_values, payload)
    await db.commit()
    return row.values


@router.get("/me")
async def get_me(db: AsyncSession = Depends(get_db), identity: dict[str, uuid.UUID] = Depends(current_identity)):
    user = (await db.execute(select(OrgUser).where(
        OrgUser.id == identity["user_id"], OrgUser.tenant_id == identity["tenant_id"]
    ))).scalar_one_or_none()
    if user is None:
        raise HTTPException(404, detail="user_not_found")
    return {"id": str(user.id), "email": user.email, "fullName": user.full_name, "language": user.language}


@router.patch("/me")
async def update_me(payload: dict[str, Any], db: AsyncSession = Depends(get_db), identity: dict[str, uuid.UUID] = Depends(current_identity)):
    allowed = {"full_name", "language", "current_password", "new_password"}
    if set(payload) - allowed:
        raise HTTPException(422, detail="Only profile fields may be updated")
    password_change = "current_password" in payload or "new_password" in payload
    if password_change:
        new_password = payload.get("new_password")
        current_password = payload.get("current_password")
        if (
            not isinstance(current_password, str)
            or not isinstance(new_password, str)
            or len(new_password) < 8
            or len(new_password.encode("utf-8")) > 72
        ):
            raise HTTPException(422, detail="current_password and a new password of 8 to 72 UTF-8 bytes are required")
    user = (await db.execute(select(OrgUser).where(
        OrgUser.id == identity["user_id"], OrgUser.tenant_id == identity["tenant_id"]
    ).with_for_update())).scalar_one_or_none()
    if user is None:
        raise HTTPException(404, detail="user_not_found")
    if password_change and not verify_password(payload["current_password"], user.password_hash):
        raise HTTPException(401, detail="current_password_incorrect")
    old = {"full_name": user.full_name, "language": user.language}
    for key in ("full_name", "language"):
        if key in payload:
            setattr(user, key, payload[key])
    if password_change:
        user.password_hash = hash_password(new_password)
        sessions = (await db.execute(select(RefreshSession).where(
            RefreshSession.tenant_id == identity["tenant_id"],
            RefreshSession.user_id == user.id,
            RefreshSession.revoked_at.is_(None),
        ).with_for_update())).scalars().all()
        for session in sessions:
            session.revoked_at = datetime.now(timezone.utc)
    await _audit(
        db, identity, "user", user.id, "update",
        old,
        {**{key: getattr(user, key) for key in ("full_name", "language")}, "passwordChanged": password_change},
    )
    await db.commit()
    return {"id": str(user.id), "email": user.email, "fullName": user.full_name, "language": user.language}


def calculate_bill(payload: dict[str, Any]) -> dict[str, Any]:
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise HTTPException(422, detail="items must contain at least one product")
    subtotal = ZERO
    for item in items:
        quantity = _decimal(item.get("qty"), "qty", minimum=Decimal("0.001"))
        unit_price = _decimal(item.get("unitPrice"), "unitPrice", minimum=Decimal("0"))
        subtotal += quantity * unit_price
    subtotal = _money(subtotal)
    discount_spec = payload.get("discount") or {"type": "NONE"}
    discount_type = str(discount_spec.get("type", "NONE")).upper()
    discount_value = _decimal(discount_spec.get("value", 0), "discount.value", minimum=Decimal("0"))
    if discount_type == "NONE":
        discount = ZERO
    elif discount_type in {"AMOUNT", "RUPEE"}:
        discount = min(_money(discount_value), subtotal)
    elif discount_type in {"PERCENT", "PERCENTAGE"}:
        if discount_value > 100:
            raise HTTPException(422, detail="discount percentage cannot exceed 100")
        discount = _money(subtotal * discount_value / 100)
    else:
        raise HTTPException(422, detail="discount.type must be NONE, AMOUNT, or PERCENT")
    net = subtotal - discount
    payment_type = str(payload.get("paymentType", "SPOT")).upper()
    if payment_type not in {"SPOT", "CREDIT", "PART"}:
        raise HTTPException(422, detail="paymentType must be SPOT, CREDIT, or PART")
    interest_spec = payload.get("interest") or {}
    rate = _decimal(interest_spec.get("ratePerMonth", 0), "interest.ratePerMonth", minimum=Decimal("0"))
    if "months" in interest_spec:
        months = _decimal(interest_spec["months"], "interest.months", minimum=Decimal("0"))
    else:
        months = Decimal("0")
        if payload.get("dueDate") and payload.get("billDate"):
            months = max(Decimal("0"), Decimal(str((date.fromisoformat(payload["dueDate"]) - date.fromisoformat(payload["billDate"])).days)) / 30)
    paid_now = _money(_decimal(payload.get("paidNow", "0"), "paidNow", minimum=Decimal("0")))
    if payment_type == "SPOT":
        interest = ZERO
    elif payment_type == "CREDIT" and paid_now != ZERO:
        raise HTTPException(422, detail="paidNow must be zero for CREDIT bills")
    if payment_type == "CREDIT":
        interest = _money(net * rate / 100 * months)
    elif payment_type == "PART":
        if paid_now > net:
            raise HTTPException(422, detail="paidNow cannot exceed the bill amount")
        interest = _money((net - paid_now) * rate / 100 * months)
    raw_total = net + interest
    total = raw_total.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    round_off = total - raw_total
    if payment_type == "SPOT":
        paid_now = total
    balance = max(ZERO, total - paid_now)
    gst_amount = ZERO
    taxable = net
    settings = payload.get("gst") or {}
    gst_rate = _decimal(settings.get("rate", "0"), "gst.rate", minimum=Decimal("0"))
    gst_mode = str(settings.get("mode", "INCLUSIVE")).upper()
    if gst_mode not in {"INCLUSIVE", "EXCLUSIVE"}:
        raise HTTPException(422, detail="gst.mode must be INCLUSIVE or EXCLUSIVE")
    if gst_rate:
        if gst_mode == "INCLUSIVE":
            taxable = _money(net / (Decimal("1") + gst_rate / 100))
            gst_amount = net - taxable
        else:
            taxable = net
            gst_amount = _money(net * gst_rate / 100)
    terms = f"Interest: {rate}% per month for {months.normalize()} months = {interest:.2f}" if interest else None
    return {
        "subtotal": f"{subtotal:.2f}",
        "discount": f"{discount:.2f}",
        "interestAmount": f"{interest:.2f}",
        "gst": {
            "mode": gst_mode,
            "taxable": f"{taxable:.2f}",
            "cgst": f"{(gst_amount / 2):.2f}",
            "sgst": f"{(gst_amount / 2):.2f}",
        },
        "roundOff": f"{round_off:.2f}",
        "total": f"{total:.2f}",
        "paidNow": f"{paid_now:.2f}",
        "balance": f"{balance:.2f}",
        "terms": terms,
    }


@router.post("/bills/preview")
async def preview_bill(payload: dict[str, Any], identity: dict[str, uuid.UUID] = Depends(current_identity)):
    return calculate_bill(payload)


@router.post("/bills", status_code=status.HTTP_201_CREATED)
async def create_bill(
    payload: dict[str, Any],
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    tenant_id = identity["tenant_id"]
    if idempotency_key:
        previous = (await db.execute(select(IdempotencyRecord).where(
            IdempotencyRecord.tenant_id == tenant_id,
            IdempotencyRecord.operation == "bill",
            IdempotencyRecord.key == idempotency_key,
        ))).scalar_one_or_none()
        if previous:
            return previous.response
    try:
        farmer_id = uuid.UUID(str(payload["farmerId"]))
    except (KeyError, ValueError) as exc:
        raise HTTPException(422, detail="farmerId is required") from exc
    await _owned(db, Farmer, tenant_id, farmer_id)
    season_id = uuid.UUID(str(payload["seasonId"])) if payload.get("seasonId") else None
    if season_id:
        await _owned(db, Season, tenant_id, season_id)
    calculation = calculate_bill(payload)
    bill_date = date.fromisoformat(payload.get("billDate", date.today().isoformat()))
    due_date = date.fromisoformat(payload["dueDate"]) if payload.get("dueDate") else None
    settings_row = await db.get(Setting, tenant_id)
    prefix = (settings_row.values if settings_row else {}).get("billNumberPrefix", "BILL")
    bill_id = uuid.uuid4()
    bill_number = f"{prefix}-{bill_date:%Y%m%d}-{str(bill_id)[:8].upper()}"
    bill = Bill(
        id=bill_id,
        tenant_id=tenant_id,
        bill_number=bill_number,
        farmer_id=farmer_id,
        season_id=season_id,
        bill_date=bill_date,
        due_date=due_date,
        payment_type=str(payload.get("paymentType", "SPOT")).upper(),
        subtotal=Decimal(calculation["subtotal"]),
        discount=Decimal(calculation["discount"]),
        interest_amount=Decimal(calculation["interestAmount"]),
        gst_amount=Decimal(calculation["gst"]["cgst"]) + Decimal(calculation["gst"]["sgst"]),
        round_off=Decimal(calculation["roundOff"]),
        total=Decimal(calculation["total"]),
        paid_now=Decimal(calculation["paidNow"]),
        balance=Decimal(calculation["balance"]),
        terms=calculation["terms"],
        status="posted",
        idempotency_key=idempotency_key,
    )
    db.add(bill)
    await db.flush()
    for line in payload["items"]:
        pack_id = uuid.UUID(str(line["packId"]))
        pack = await _owned(db, Pack, tenant_id, pack_id, lock=True)
        quantity = _decimal(line["qty"], "qty", minimum=Decimal("0.001"))
        is_loose_sale = bool(line.get("looseSale", False))
        if is_loose_sale and not pack.allow_loose_sale:
            raise HTTPException(422, detail="loose sale is not enabled for this pack")
        quantity_base = quantity if is_loose_sale else quantity * pack.size_in_base_unit
        balance = await db.scalar(select(func.coalesce(func.sum(StockMovement.quantity_base), 0)).where(
            StockMovement.tenant_id == tenant_id, StockMovement.pack_id == pack_id
        ))
        if Decimal(str(balance or 0)) < quantity_base and payload.get("allowNegative") is not True:
            raise HTTPException(409, detail=f"insufficient_stock:{pack_id}")
        product = await _owned(db, Product, tenant_id, pack.product_id)
        unit_price = _decimal(line["unitPrice"], "unitPrice", minimum=Decimal("0"))
        db.add(BillItem(
            tenant_id=tenant_id,
            bill_id=bill.id,
            pack_id=pack.id,
            product_name=product.name,
            pack_name=f"{pack.size} {pack.size_unit}",
            quantity=quantity,
            quantity_base=quantity_base,
            unit_price=unit_price,
            line_total=_money(quantity * unit_price),
        ))
        remaining_from_lots = quantity_base
        lots = (await db.execute(select(StockLot).where(
            StockLot.tenant_id == tenant_id,
            StockLot.pack_id == pack.id,
            StockLot.available_base > 0,
        ).order_by(
            StockLot.expiry_date.asc().nulls_last(), StockLot.received_date, StockLot.id
        ).with_for_update())).scalars().all()
        for lot in lots:
            if remaining_from_lots <= ZERO:
                break
            consumed = min(lot.available_base, remaining_from_lots)
            lot.available_base -= consumed
            remaining_from_lots -= consumed
            db.add(StockMovement(
                tenant_id=tenant_id,
                pack_id=pack.id,
                stock_lot_id=lot.id,
                movement_type="sale",
                quantity_base=-consumed,
                source_id=bill.id,
                source_type="bill",
            ))
        if remaining_from_lots > ZERO:
            db.add(StockMovement(
                tenant_id=tenant_id,
                pack_id=pack.id,
                movement_type="sale",
                quantity_base=-remaining_from_lots,
                source_id=bill.id,
                source_type="bill",
            ))
    db.add(KhataEntry(
        tenant_id=tenant_id,
        farmer_id=farmer_id,
        bill_id=bill.id,
        entry_type="bill",
        debit=bill.total,
        credit=ZERO,
        description=f"Bill {bill_number}",
    ))
    if bill.paid_now > ZERO:
        payment = Payment(
            tenant_id=tenant_id,
            farmer_id=farmer_id,
            bill_id=bill.id,
            amount=bill.paid_now,
            mode=str(payload.get("paymentMode", "cash")).lower(),
            payment_date=bill_date,
        )
        db.add(payment)
        await db.flush()
        db.add(PaymentAllocation(
            tenant_id=tenant_id,
            payment_id=payment.id,
            bill_id=bill.id,
            interest_amount=min(bill.paid_now, bill.interest_amount),
            principal_amount=max(ZERO, bill.paid_now - bill.interest_amount),
        ))
        db.add(KhataEntry(
            tenant_id=tenant_id,
            farmer_id=farmer_id,
            bill_id=bill.id,
            payment_id=payment.id,
            entry_type="payment",
            debit=ZERO,
            credit=bill.paid_now,
            description=f"Payment for {bill_number}",
        ))
    await _audit(db, identity, "bill", bill.id, "create", None, _row(bill))
    result = {**_row(bill), "items": []}
    for item in (await db.execute(select(BillItem).where(BillItem.tenant_id == tenant_id, BillItem.bill_id == bill.id))).scalars():
        result["items"].append(_row(item))
    try:
        if idempotency_key:
            db.add(IdempotencyRecord(
                tenant_id=tenant_id, operation="bill", key=idempotency_key, response=result
            ))
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, detail="bill_conflict") from exc
    return result


@router.get("/bills")
async def list_bills(
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=100),
    q: str | None = None,
    sort: str = "bill_date:desc",
    farmerId: uuid.UUID | None = None,
    seasonId: uuid.UUID | None = None,
    paymentType: str | None = None,
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    statement = select(Bill).where(Bill.tenant_id == identity["tenant_id"])
    if q:
        statement = statement.join(Farmer, (Farmer.id == Bill.farmer_id) & (Farmer.tenant_id == Bill.tenant_id)).where(
            or_(Bill.bill_number.ilike(f"%{q}%"), Farmer.name.ilike(f"%{q}%"))
        )
    if farmerId:
        statement = statement.where(Bill.farmer_id == farmerId)
    if seasonId:
        statement = statement.where(Bill.season_id == seasonId)
    if paymentType:
        statement = statement.where(Bill.payment_type == paymentType.upper())
    if from_date:
        statement = statement.where(Bill.bill_date >= from_date)
    if to_date:
        statement = statement.where(Bill.bill_date <= to_date)
    field, separator, direction = sort.partition(":")
    if not separator or field not in {"bill_date", "bill_number", "total", "balance", "created_at"} or direction not in {"asc", "desc"}:
        raise HTTPException(422, detail="sort must use bill_date, bill_number, total, balance, or created_at")
    sort_column = getattr(Bill, field)
    if status_filter:
        statement = statement.where(Bill.status == status_filter)
    total = await db.scalar(select(func.count()).select_from(statement.subquery()))
    bills = (await db.execute(statement.order_by(sort_column.asc() if direction == "asc" else sort_column.desc()).offset((page - 1) * pageSize).limit(pageSize))).scalars().all()
    return {"items": [_row(item) for item in bills], "page": page, "pageSize": pageSize, "total": total or 0}


@router.get("/bills/{bill_id}")
async def get_bill(bill_id: uuid.UUID, db: AsyncSession = Depends(get_db), identity: dict[str, uuid.UUID] = Depends(current_identity)):
    bill = await _owned(db, Bill, identity["tenant_id"], bill_id)
    lines = (await db.execute(select(BillItem).where(BillItem.tenant_id == identity["tenant_id"], BillItem.bill_id == bill_id))).scalars().all()
    return {**_row(bill), "items": [_row(item) for item in lines]}


@router.get("/bills/{bill_id:uuid}/pdf")
async def bill_pdf(
    bill_id: uuid.UUID,
    format: str = Query("a4", pattern="^(a4|thermal)$"),
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    bill = await _owned(db, Bill, identity["tenant_id"], bill_id)
    farmer = await _owned(db, Farmer, identity["tenant_id"], bill.farmer_id)
    lines = (await db.execute(select(BillItem).where(
        BillItem.tenant_id == identity["tenant_id"], BillItem.bill_id == bill_id
    ))).scalars().all()
    body = [
        f"Bill: {bill.bill_number}",
        f"Date: {bill.bill_date.isoformat()}",
        f"Farmer: {farmer.name} ({farmer.mobile})",
        "",
    ]
    body.extend(f"{item.product_name} {item.pack_name} x {item.quantity} @ {item.unit_price:.2f} = {item.line_total:.2f}" for item in lines)
    body.extend([
        "",
        f"Subtotal: {bill.subtotal:.2f}",
        f"Discount: {bill.discount:.2f}",
        f"Interest: {bill.interest_amount:.2f}",
        f"Total: {bill.total:.2f}",
        f"Paid: {bill.paid_now:.2f}",
        f"Balance: {bill.balance:.2f}",
    ])
    if format == "thermal":
        body = [line[:44] for line in body]
    return _pdf_response(f"Ferti+ Invoice ({format})", body, f"{bill.bill_number}.pdf")


@router.post("/bills/{bill_id:uuid}/share")
async def share_bill(
    bill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    bill = await _owned(db, Bill, identity["tenant_id"], bill_id)
    farmer = await _owned(db, Farmer, identity["tenant_id"], bill.farmer_id)
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    token = jwt.encode(
        {"sub": str(bill.id), "tid": str(identity["tenant_id"]), "purpose": "bill_pdf", "exp": expires},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    pdf_url = f"{settings.PUBLIC_API_URL.rstrip('/')}/api/v1/public/bills/{bill.id}/pdf?token={token}"
    message = f"Ferti+ bill {bill.bill_number}: Rs. {bill.total:.2f}. PDF: {pdf_url}"
    import urllib.parse

    return {
        "whatsappUrl": f"https://wa.me/{farmer.mobile.lstrip('+')}?text={urllib.parse.quote(message)}",
        "pdfUrl": pdf_url,
        "expiresAt": expires.isoformat(),
    }


@router.get("/public/bills/{bill_id:uuid}/pdf")
async def public_bill_pdf(
    bill_id: uuid.UUID,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        claims = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        tenant_id = uuid.UUID(claims["tid"])
        if claims.get("purpose") != "bill_pdf" or claims.get("sub") != str(bill_id):
            raise ValueError("invalid share token")
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(401, detail="invalid_or_expired_share_link") from exc
    bill = await _owned(db, Bill, tenant_id, bill_id)
    lines = (await db.execute(select(BillItem).where(
        BillItem.tenant_id == tenant_id, BillItem.bill_id == bill_id
    ))).scalars().all()
    body = [f"Bill: {bill.bill_number}", f"Date: {bill.bill_date.isoformat()}"]
    body.extend(f"{item.product_name} {item.pack_name} x {item.quantity} = {item.line_total:.2f}" for item in lines)
    body.extend([f"Total: {bill.total:.2f}", f"Balance: {bill.balance:.2f}"])
    return _pdf_response(f"Ferti+ Invoice {bill.bill_number}", body, f"{bill.bill_number}.pdf")


@router.get("/farmers/{farmer_id}/summary")
async def farmer_summary(farmer_id: uuid.UUID, db: AsyncSession = Depends(get_db), identity: dict[str, uuid.UUID] = Depends(current_identity)):
    await _owned(db, Farmer, identity["tenant_id"], farmer_id)
    bills = (await db.execute(select(Bill).where(Bill.tenant_id == identity["tenant_id"], Bill.farmer_id == farmer_id, Bill.status == "posted"))).scalars().all()
    last_payment = await db.scalar(select(func.max(Payment.payment_date)).where(Payment.tenant_id == identity["tenant_id"], Payment.farmer_id == farmer_id))
    last_bill = await db.scalar(select(func.max(Bill.bill_date)).where(Bill.tenant_id == identity["tenant_id"], Bill.farmer_id == farmer_id, Bill.status == "posted"))
    outstanding = sum((bill.balance for bill in bills), ZERO)
    overdue = sum((bill.balance for bill in bills if bill.due_date and bill.due_date < date.today()), ZERO)
    return {
        "totalBilled": f"{sum((bill.total for bill in bills), ZERO):.2f}",
        "paid": f"{sum((bill.paid_now for bill in bills), ZERO):.2f}",
        "outstanding": f"{outstanding:.2f}",
        "overdue": f"{overdue:.2f}",
        "lastBillDate": last_bill.isoformat() if last_bill else None,
        "lastPaymentDate": last_payment.isoformat() if last_payment else None,
    }


@router.get("/seasons/current")
async def current_season(db: AsyncSession = Depends(get_db), identity: dict[str, uuid.UUID] = Depends(current_identity)):
    season = (await db.execute(select(Season).where(
        Season.tenant_id == identity["tenant_id"], Season.start_date <= date.today(), Season.end_date >= date.today()
    ).order_by(Season.start_date.desc()))).scalars().first()
    return _row(season) if season else None


@router.post("/stock/receipts", status_code=status.HTTP_201_CREATED)
async def receive_stock(
    payload: dict[str, Any],
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    tenant_id = identity["tenant_id"]
    if idempotency_key:
        previous = (await db.execute(select(IdempotencyRecord).where(
            IdempotencyRecord.tenant_id == tenant_id,
            IdempotencyRecord.operation == "stock_receipt",
            IdempotencyRecord.key == idempotency_key,
        ))).scalar_one_or_none()
        if previous:
            return previous.response
    lines = payload.get("lines")
    if not isinstance(lines, list) or not lines:
        raise HTTPException(422, detail="lines must contain at least one receipt line")
    received_date = date.fromisoformat(payload.get("date", date.today().isoformat()))
    receipt_id = uuid.uuid4()
    movements = []
    for line in lines:
        pack = await _owned(db, Pack, tenant_id, uuid.UUID(str(line["packId"])), lock=True)
        quantity = _decimal(line["qty"], "qty", minimum=Decimal("0.001"))
        base_quantity = quantity * pack.size_in_base_unit
        expiry = date.fromisoformat(line["expiry"]) if line.get("expiry") else None
        lot_id = uuid.uuid4()
        lot = StockLot(
            id=lot_id,
            tenant_id=tenant_id,
            pack_id=pack.id,
            supplier=payload.get("supplier"),
            received_date=received_date,
            quantity_base=base_quantity,
            available_base=base_quantity,
            cost_price=_decimal(line["costPrice"], "costPrice", minimum=Decimal("0")),
            batch_number=line.get("batch"),
            expiry_date=expiry,
        )
        movement = StockMovement(
            tenant_id=tenant_id,
            pack_id=pack.id,
            stock_lot_id=lot_id,
            movement_type="in",
            quantity_base=base_quantity,
            reason="stock receipt",
            source_id=receipt_id,
            source_type="receipt",
        )
        db.add_all([lot, movement])
        movements.append({"packId": str(pack.id), "quantityBase": str(base_quantity)})
    result = {"id": str(receipt_id), "receivedDate": received_date.isoformat(), "lines": movements}
    try:
        await _audit(db, identity, "stock_receipt", receipt_id, "create", None, result)
        if idempotency_key:
            db.add(IdempotencyRecord(
                tenant_id=tenant_id, operation="stock_receipt", key=idempotency_key, response=result
            ))
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, detail="stock_receipt_conflict") from exc
    return result


@router.post("/stock/adjustments", status_code=status.HTTP_201_CREATED)
async def adjust_stock(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    reason = str(payload.get("reason", "")).strip()
    if not reason:
        raise HTTPException(422, detail="reason is required")
    try:
        lines = payload["lines"]
    except KeyError as exc:
        raise HTTPException(422, detail="lines are required") from exc
    if not isinstance(lines, list) or not lines:
        raise HTTPException(422, detail="lines must contain at least one adjustment")
    adjustment_type = str(payload.get("type", "correction")).lower()
    if adjustment_type not in {"damage", "loss", "correction"}:
        raise HTTPException(422, detail="type must be damage, loss, or correction")
    adjustment_id = uuid.uuid4()
    results = []
    for line in lines:
        pack = await _owned(db, Pack, identity["tenant_id"], uuid.UUID(str(line["packId"])), lock=True)
        amount = _decimal(line["qty"], "qty", minimum=Decimal("0.001")) * pack.size_in_base_unit
        direction = str(line.get("direction", "out")).lower()
        if direction not in {"in", "out"}:
            raise HTTPException(422, detail="direction must be in or out")
        if adjustment_type in {"damage", "loss"} and direction != "out":
            raise HTTPException(422, detail="damage and loss adjustments must be outbound")
        delta = amount if direction == "in" else -amount
        balance = await db.scalar(select(func.coalesce(func.sum(StockMovement.quantity_base), 0)).where(
            StockMovement.tenant_id == identity["tenant_id"], StockMovement.pack_id == pack.id
        ))
        if Decimal(str(balance or 0)) + delta < 0:
            raise HTTPException(409, detail="adjustment_would_make_stock_negative")
        if delta > 0:
            lot_id = uuid.uuid4()
            db.add(StockLot(
                id=lot_id,
                tenant_id=identity["tenant_id"],
                pack_id=pack.id,
                supplier="stock adjustment",
                received_date=date.today(),
                quantity_base=delta,
                available_base=delta,
                cost_price=_decimal(line.get("costPrice", "0"), "costPrice", minimum=ZERO),
                batch_number=line.get("batch"),
                expiry_date=date.fromisoformat(line["expiry"]) if line.get("expiry") else None,
            ))
            db.add(StockMovement(
                tenant_id=identity["tenant_id"], pack_id=pack.id, stock_lot_id=lot_id,
                movement_type=adjustment_type, quantity_base=delta, reason=reason,
                source_id=adjustment_id, source_type="adjustment",
            ))
        else:
            remaining = -delta
            lots = (await db.execute(select(StockLot).where(
                StockLot.tenant_id == identity["tenant_id"],
                StockLot.pack_id == pack.id,
                StockLot.available_base > 0,
            ).order_by(
                StockLot.expiry_date.asc().nulls_last(), StockLot.received_date, StockLot.id
            ).with_for_update())).scalars().all()
            for lot in lots:
                if remaining <= ZERO:
                    break
                removed = min(lot.available_base, remaining)
                lot.available_base -= removed
                remaining -= removed
                db.add(StockMovement(
                    tenant_id=identity["tenant_id"], pack_id=pack.id, stock_lot_id=lot.id,
                    movement_type=adjustment_type, quantity_base=-removed, reason=reason,
                    source_id=adjustment_id, source_type="adjustment",
                ))
            if remaining > ZERO:
                db.add(StockMovement(
                    tenant_id=identity["tenant_id"], pack_id=pack.id,
                    movement_type=adjustment_type, quantity_base=-remaining, reason=reason,
                    source_id=adjustment_id, source_type="adjustment",
                ))
        results.append({"packId": str(pack.id), "quantityBase": str(delta)})
    result = {"id": str(adjustment_id), "reason": reason, "lines": results}
    await _audit(db, identity, "stock_adjustment", adjustment_id, "create", None, result)
    await db.commit()
    return result


@router.get("/stock")
async def current_stock(
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    base = select(Pack).where(Pack.tenant_id == identity["tenant_id"], Pack.active.is_(True))
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    packs = (await db.execute(base.order_by(Pack.product_id, Pack.size_in_base_unit).offset((page - 1) * pageSize).limit(pageSize))).scalars().all()
    balances = dict((await db.execute(
        select(StockMovement.pack_id, func.coalesce(func.sum(StockMovement.quantity_base), 0))
        .where(
            StockMovement.tenant_id == identity["tenant_id"],
            StockMovement.pack_id.in_([pack.id for pack in packs]),
        )
        .group_by(StockMovement.pack_id)
    )).all()) if packs else {}
    items = [
        {
            **_row(pack),
            "stockBase": str(balances.get(pack.id, 0)),
            "stockPacks": str(Decimal(str(balances.get(pack.id, 0))) / pack.size_in_base_unit),
        }
        for pack in packs
    ]
    return {"items": items, "page": page, "pageSize": pageSize, "total": total or 0}


@router.get("/stock/ledger")
async def stock_ledger(
    packId: uuid.UUID,
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    await _owned(db, Pack, identity["tenant_id"], packId)
    entries = (await db.execute(select(StockMovement).where(
        StockMovement.tenant_id == identity["tenant_id"], StockMovement.pack_id == packId
    ).order_by(StockMovement.created_at, StockMovement.id))).scalars().all()
    balance = ZERO
    result = []
    for entry in entries:
        balance += entry.quantity_base
        result.append({**_row(entry), "balance": str(balance)})
    offset = (page - 1) * pageSize
    return {"items": result[offset:offset + pageSize], "page": page, "pageSize": pageSize, "total": len(result)}


@router.get("/stock/alerts")
async def stock_alerts(db: AsyncSession = Depends(get_db), identity: dict[str, uuid.UUID] = Depends(current_identity)):
    products = (await db.execute(select(Product).where(Product.tenant_id == identity["tenant_id"], Product.active.is_(True)))).scalars().all()
    product_ids = [product.id for product in products]
    packs = (await db.execute(select(Pack).where(
        Pack.tenant_id == identity["tenant_id"], Pack.product_id.in_(product_ids), Pack.active.is_(True)
    ))).scalars().all() if product_ids else []
    stock = dict((await db.execute(
        select(StockMovement.pack_id, func.coalesce(func.sum(StockMovement.quantity_base), 0))
        .where(
            StockMovement.tenant_id == identity["tenant_id"],
            StockMovement.pack_id.in_([pack.id for pack in packs]),
        )
        .group_by(StockMovement.pack_id)
    )).all()) if packs else {}
    stock_by_product: dict[uuid.UUID, Decimal] = {}
    for pack in packs:
        stock_by_product[pack.product_id] = stock_by_product.get(pack.product_id, ZERO) + Decimal(str(stock.get(pack.id, 0)))
    low_stock = [
        {"productId": str(product.id), "name": product.name, "stockBase": str(stock_by_product.get(product.id, ZERO))}
        for product in products
        if stock_by_product.get(product.id, ZERO) <= product.low_stock_level
    ]
    near_expiry = (await db.execute(select(StockLot).where(
        StockLot.tenant_id == identity["tenant_id"],
        StockLot.expiry_date >= date.today(),
        StockLot.expiry_date <= date.today() + timedelta(days=30),
        StockLot.available_base > 0,
    ).order_by(StockLot.expiry_date))).scalars().all()
    return {"lowStock": low_stock, "nearExpiry": [_row(lot) for lot in near_expiry]}


@router.post("/payments", status_code=status.HTTP_201_CREATED)
async def create_payment(
    payload: dict[str, Any],
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    tenant_id = identity["tenant_id"]
    if idempotency_key:
        previous = (await db.execute(select(IdempotencyRecord).where(
            IdempotencyRecord.tenant_id == tenant_id,
            IdempotencyRecord.operation == "payment",
            IdempotencyRecord.key == idempotency_key,
        ))).scalar_one_or_none()
        if previous:
            return previous.response
    farmer_id = uuid.UUID(str(payload["farmerId"]))
    await _owned(db, Farmer, tenant_id, farmer_id)
    amount = _money(_decimal(payload["amount"], "amount", minimum=CENT))
    mode = str(payload.get("mode", "")).lower()
    if mode not in {"cash", "upi", "bank"}:
        raise HTTPException(422, detail="mode must be cash, upi, or bank")
    payment_date = date.fromisoformat(payload.get("date", date.today().isoformat()))
    named_bill_id = uuid.UUID(str(payload["billId"])) if payload.get("billId") else None
    if named_bill_id:
        named_bill = await _owned(db, Bill, tenant_id, named_bill_id, lock=True)
        if named_bill.farmer_id != farmer_id or named_bill.status != "posted":
            raise HTTPException(422, detail="bill is not payable by this farmer")
        bills = [named_bill]
    else:
        bills = (await db.execute(select(Bill).where(
            Bill.tenant_id == tenant_id,
            Bill.farmer_id == farmer_id,
            Bill.status == "posted",
            Bill.balance > 0,
        ).order_by(Bill.bill_date, Bill.created_at).with_for_update())).scalars().all()
    payment = Payment(
        tenant_id=tenant_id,
        farmer_id=farmer_id,
        amount=amount,
        mode=mode,
        payment_date=payment_date,
        bill_id=named_bill_id,
        idempotency_key=idempotency_key,
    )
    db.add(payment)
    await db.flush()
    remaining = amount
    allocations = []
    for bill in bills:
        if remaining <= ZERO:
            break
        applied = min(remaining, bill.balance)
        previously_paid_interest = await db.scalar(select(func.coalesce(func.sum(PaymentAllocation.interest_amount), 0)).where(
            PaymentAllocation.tenant_id == tenant_id, PaymentAllocation.bill_id == bill.id
        ))
        interest_due = max(ZERO, bill.interest_amount - Decimal(str(previously_paid_interest or 0)))
        interest_paid = min(applied, interest_due)
        principal_paid = applied - interest_paid
        bill.balance -= applied
        bill.paid_now += applied
        db.add(PaymentAllocation(
            tenant_id=tenant_id,
            payment_id=payment.id,
            bill_id=bill.id,
            interest_amount=interest_paid,
            principal_amount=principal_paid,
        ))
        db.add(KhataEntry(
            tenant_id=tenant_id,
            farmer_id=farmer_id,
            bill_id=bill.id,
            payment_id=payment.id,
            entry_type="payment",
            debit=ZERO,
            credit=applied,
            description=f"Payment received for bill {bill.bill_number}",
        ))
        allocations.append({"billId": str(bill.id), "amount": f"{applied:.2f}", "interest": f"{interest_paid:.2f}", "principal": f"{principal_paid:.2f}"})
        remaining -= applied
    if remaining > ZERO and named_bill_id:
        raise HTTPException(409, detail="payment_exceeds_bill_balance")
    if remaining > ZERO:
        db.add(KhataEntry(
            tenant_id=tenant_id,
            farmer_id=farmer_id,
            payment_id=payment.id,
            entry_type="payment",
            debit=ZERO,
            credit=remaining,
            description="Unallocated farmer payment",
        ))
    if mode == "cash":
        db.add(CashbookEntry(
            tenant_id=tenant_id, entry_date=payment_date, direction="in", amount=amount,
            category="farmer_payment", description=f"Payment from farmer {farmer_id}",
        ))
    result = {**_row(payment), "allocations": allocations, "unallocated": f"{remaining:.2f}"}
    try:
        await _audit(db, identity, "payment", payment.id, "create", None, result)
        if idempotency_key:
            db.add(IdempotencyRecord(
                tenant_id=tenant_id, operation="payment", key=idempotency_key, response=result
            ))
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, detail="payment_conflict") from exc
    return result


@router.post("/bills/{bill_id:uuid}/cancel")
async def cancel_bill(
    bill_id: uuid.UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    reason = str(payload.get("reason", "")).strip()
    if not reason:
        raise HTTPException(422, detail="reason is required")
    bill = await _owned(db, Bill, identity["tenant_id"], bill_id, lock=True)
    if bill.status != "posted":
        raise HTTPException(409, detail="bill_is_not_posted")
    stock_sales = (await db.execute(select(StockMovement).where(
        StockMovement.tenant_id == identity["tenant_id"],
        StockMovement.source_id == bill.id,
        StockMovement.source_type == "bill",
        StockMovement.movement_type == "sale",
    ))).scalars().all()
    for movement in stock_sales:
        if movement.stock_lot_id:
            lot = await _owned(db, StockLot, identity["tenant_id"], movement.stock_lot_id, lock=True)
            lot.available_base += -movement.quantity_base
        db.add(StockMovement(
            tenant_id=identity["tenant_id"], pack_id=movement.pack_id, stock_lot_id=movement.stock_lot_id,
            movement_type="return", quantity_base=-movement.quantity_base, reason=reason,
            source_id=bill.id, source_type="bill_cancel",
        ))
    original_entries = (await db.execute(select(KhataEntry).where(
        KhataEntry.tenant_id == identity["tenant_id"], KhataEntry.bill_id == bill.id
    ))).scalars().all()
    for entry in original_entries:
        db.add(KhataEntry(
            tenant_id=identity["tenant_id"],
            farmer_id=bill.farmer_id,
            bill_id=bill.id,
            entry_type="reversal",
            debit=entry.credit,
            credit=entry.debit,
            description=f"Reversal: {reason}",
            reverses_entry_id=entry.id,
        ))
    old = _row(bill)
    bill.status = "cancelled"
    bill.version += 1
    bill.balance = ZERO
    await _audit(db, identity, "bill", bill.id, "cancel", old, {**old, "status": "cancelled", "cancelReason": reason})
    await db.commit()
    return {"id": str(bill.id), "status": bill.status}


@router.post("/bills/drafts", status_code=status.HTTP_201_CREATED)
async def create_bill_draft(payload: dict[str, Any], db: AsyncSession = Depends(get_db), identity: dict[str, uuid.UUID] = Depends(current_identity)):
    draft = BillDraft(tenant_id=identity["tenant_id"], owner_id=identity["user_id"], payload=payload)
    db.add(draft)
    await db.commit()
    await db.refresh(draft)
    await _audit(db, identity, "bill_draft", draft.id, "create", None, {"payload": payload})
    await db.commit()
    return {"id": str(draft.id), "payload": draft.payload, "createdAt": draft.created_at.isoformat()}


@router.get("/bills/drafts")
async def list_bill_drafts(db: AsyncSession = Depends(get_db), identity: dict[str, uuid.UUID] = Depends(current_identity)):
    drafts = (await db.execute(select(BillDraft).where(
        BillDraft.tenant_id == identity["tenant_id"], BillDraft.owner_id == identity["user_id"]
    ).order_by(BillDraft.created_at.desc()))).scalars().all()
    return {"items": [{"id": str(row.id), "payload": row.payload, "createdAt": row.created_at.isoformat()} for row in drafts]}


@router.get("/farmers/{farmer_id:uuid}/khata")
async def farmer_khata(
    farmer_id: uuid.UUID,
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=100),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    seasonId: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    await _owned(db, Farmer, identity["tenant_id"], farmer_id)
    statement = select(KhataEntry).where(
        KhataEntry.tenant_id == identity["tenant_id"], KhataEntry.farmer_id == farmer_id
    ).order_by(KhataEntry.created_at, KhataEntry.id)
    season_bill_ids = None
    if seasonId:
        season_bill_ids = set((await db.scalars(select(Bill.id).where(
            Bill.tenant_id == identity["tenant_id"], Bill.season_id == seasonId
        ))).all())
    entries = (await db.execute(statement)).scalars().all()
    balance = ZERO
    filtered_entries = []
    for entry in entries:
        balance += entry.debit - entry.credit
        entry_date = entry.created_at.date()
        if from_date and entry_date < from_date:
            continue
        if to_date and entry_date > to_date:
            continue
        if season_bill_ids is not None and entry.bill_id not in season_bill_ids:
            continue
        filtered_entries.append({**_row(entry), "balance": f"{balance:.2f}"})
    offset = (page - 1) * pageSize
    return {
        "items": filtered_entries[offset:offset + pageSize],
        "page": page,
        "pageSize": pageSize,
        "total": len(filtered_entries),
    }


@router.get("/farmers/{farmer_id:uuid}/khata/export")
async def export_farmer_khata(
    farmer_id: uuid.UUID,
    format: str = Query(..., pattern="^(pdf|xlsx)$"),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    await _owned(db, Farmer, identity["tenant_id"], farmer_id)
    statement = select(KhataEntry).where(
        KhataEntry.tenant_id == identity["tenant_id"], KhataEntry.farmer_id == farmer_id
    ).order_by(KhataEntry.created_at, KhataEntry.id)
    entries = (await db.execute(statement)).scalars().all()
    balance = ZERO
    rows = []
    for entry in entries:
        balance += entry.debit - entry.credit
        entry_date = entry.created_at.date()
        if from_date and entry_date < from_date:
            continue
        if to_date and entry_date > to_date:
            continue
        rows.append([entry.created_at.date(), entry.entry_type, entry.description, entry.debit, entry.credit, balance])
    return _export_response(format, "Farmer Khata", ["Date", "Type", "Description", "Debit", "Credit", "Balance"], rows, f"farmer-{farmer_id}-khata")


@router.post("/farmers/{farmer_id:uuid}/adjustments", status_code=status.HTTP_201_CREATED)
async def farmer_adjustment(
    farmer_id: uuid.UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    await _owned(db, Farmer, identity["tenant_id"], farmer_id)
    reason = str(payload.get("reason", "")).strip()
    adjustment_type = str(payload.get("type", "")).lower()
    if not reason or adjustment_type not in {"discount", "write_off", "correction"}:
        raise HTTPException(422, detail="type and reason are required")
    amount = _money(_decimal(payload.get("amount"), "amount", minimum=CENT))
    direction = str(payload.get("direction", "credit" if adjustment_type != "correction" else "")).lower()
    if direction not in {"debit", "credit"}:
        raise HTTPException(422, detail="correction direction must be debit or credit")
    entry = KhataEntry(
        tenant_id=identity["tenant_id"], farmer_id=farmer_id, entry_type=adjustment_type,
        debit=amount if direction == "debit" else ZERO,
        credit=amount if direction == "credit" else ZERO,
        description=reason,
    )
    db.add(entry)
    await db.flush()
    await _audit(db, identity, "farmer_adjustment", entry.id, "create", None, _row(entry))
    await db.commit()
    await db.refresh(entry)
    return _row(entry)


@router.post("/farmers/{farmer_id:uuid}/reminders")
async def farmer_reminder(
    farmer_id: uuid.UUID,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    farmer = await _owned(db, Farmer, identity["tenant_id"], farmer_id)
    channel = str(payload.get("channel", "whatsapp")).lower()
    if channel not in {"sms", "whatsapp"}:
        raise HTTPException(422, detail="channel must be sms or whatsapp")
    outstanding = await db.scalar(select(func.coalesce(func.sum(Bill.balance), 0)).where(
        Bill.tenant_id == identity["tenant_id"], Bill.farmer_id == farmer.id, Bill.status == "posted"
    ))
    message = f"Namaste {farmer.name}, your outstanding balance is Rs. {Decimal(str(outstanding or 0)):.2f}. Please contact the shop for details."
    import urllib.parse
    link = f"https://wa.me/{farmer.mobile.lstrip('+')}?text={urllib.parse.quote(message)}" if channel == "whatsapp" else None
    return {"channel": channel, "message": message, "shareUrl": link, "sent": False}


@router.get("/khata/dues")
async def khata_dues(
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=100),
    q: str | None = None,
    sort: str = "outstanding:desc",
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    tenant_id = identity["tenant_id"]
    today = date.today()
    due = select(
        Bill.farmer_id.label("farmer_id"),
        func.sum(Bill.balance).label("balance"),
        func.max(case(
            (Bill.due_date < today, today - Bill.due_date),
            else_=0,
        )).label("overdue_days"),
    ).where(
        Bill.tenant_id == tenant_id, Bill.status == "posted", Bill.balance > 0
    ).group_by(Bill.farmer_id).subquery()
    last_payment = select(
        Payment.farmer_id.label("farmer_id"),
        func.max(Payment.payment_date).label("last_payment"),
    ).where(Payment.tenant_id == tenant_id).group_by(Payment.farmer_id).subquery()
    statement = select(
        Farmer, due.c.balance, due.c.overdue_days, last_payment.c.last_payment
    ).join(due, due.c.farmer_id == Farmer.id).outerjoin(
        last_payment, last_payment.c.farmer_id == Farmer.id
    ).where(Farmer.tenant_id == tenant_id, Farmer.active.is_(True))
    if q:
        statement = statement.where(or_(Farmer.name.ilike(f"%{q}%"), Farmer.mobile.ilike(f"%{q}%"), Farmer.village.ilike(f"%{q}%")))
    field, separator, direction = sort.partition(":")
    sort_columns = {
        "name": Farmer.name,
        "outstanding": due.c.balance,
        "overdueDays": due.c.overdue_days,
        "lastPaymentDate": last_payment.c.last_payment,
    }
    if not separator or field not in sort_columns or direction not in {"asc", "desc"}:
        raise HTTPException(422, detail="sort must use name, outstanding, overdueDays, or lastPaymentDate")
    total = await db.scalar(select(func.count()).select_from(statement.order_by(None).subquery()))
    rows = (await db.execute(statement.order_by(
        sort_columns[field].asc() if direction == "asc" else sort_columns[field].desc()
    ).offset((page - 1) * pageSize).limit(pageSize))).all()
    items = [
        {
            "farmerId": str(farmer.id),
            "name": farmer.name,
            "mobile": farmer.mobile,
            "outstanding": f"{balance:.2f}",
            "overdueDays": int(overdue_days or 0),
            "lastPaymentDate": last_payment_date.isoformat() if last_payment_date else None,
        }
        for farmer, balance, overdue_days, last_payment_date in rows
    ]
    return {"items": items, "page": page, "pageSize": pageSize, "total": total or 0}


@router.get("/dashboard/summary")
async def dashboard_summary(db: AsyncSession = Depends(get_db), identity: dict[str, uuid.UUID] = Depends(current_identity)):
    tenant_id = identity["tenant_id"]
    today = date.today()
    bills = (await db.execute(select(Bill).where(
        Bill.tenant_id == tenant_id, Bill.bill_date == today, Bill.status == "posted"
    ))).scalars().all()
    cash_in = await db.scalar(select(func.coalesce(func.sum(CashbookEntry.amount), 0)).where(
        CashbookEntry.tenant_id == tenant_id, CashbookEntry.entry_date == today,
        CashbookEntry.direction == "in"
    ))
    low = await stock_alerts(db, identity)
    credit_outstanding = await db.scalar(select(func.coalesce(func.sum(Bill.balance), 0)).where(
        Bill.tenant_id == tenant_id, Bill.status == "posted"
    ))
    dues_this_week = await db.scalar(select(func.coalesce(func.sum(Bill.balance), 0)).where(
        Bill.tenant_id == tenant_id, Bill.status == "posted", Bill.balance > 0,
        Bill.due_date <= today + timedelta(days=7),
    ))
    recent = (await db.execute(select(Bill).where(
        Bill.tenant_id == tenant_id, Bill.status == "posted"
    ).order_by(Bill.created_at.desc()).limit(5))).scalars().all()
    return {
        "todaySales": f"{sum((bill.total for bill in bills), ZERO):.2f}",
        "cashInHand": f"{Decimal(str(cash_in or 0)):.2f}",
        "creditOutstanding": f"{Decimal(str(credit_outstanding or 0)):.2f}",
        "lowStockCount": len(low["lowStock"]),
        "duesThisWeek": f"{Decimal(str(dues_this_week or 0)):.2f}",
        "recentBills": [_row(bill) for bill in recent],
    }

@router.get("/reports/sales")
async def report_sales(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    format: str | None = Query(None, pattern="^(xlsx)$"),
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    if from_date > to_date:
        raise HTTPException(422, detail="from must be on or before to")
    bills = (await db.execute(select(Bill).where(
        Bill.tenant_id == identity["tenant_id"], Bill.bill_date >= from_date,
        Bill.bill_date <= to_date, Bill.status == "posted"
    ).order_by(Bill.bill_date))).scalars().all()
    by_day: dict[str, Decimal] = {}
    for bill in bills:
        key = bill.bill_date.isoformat()
        by_day[key] = by_day.get(key, ZERO) + bill.total
    lines = (await db.execute(
        select(BillItem, Product, Brand, Category)
        .join(Bill, (Bill.id == BillItem.bill_id) & (Bill.tenant_id == BillItem.tenant_id))
        .join(Pack, (Pack.id == BillItem.pack_id) & (Pack.tenant_id == BillItem.tenant_id))
        .join(Product, (Product.id == Pack.product_id) & (Product.tenant_id == Pack.tenant_id))
        .outerjoin(Brand, (Brand.id == Product.brand_id) & (Brand.tenant_id == Product.tenant_id))
        .outerjoin(Category, (Category.id == Product.category_id) & (Category.tenant_id == Product.tenant_id))
        .where(
            BillItem.tenant_id == identity["tenant_id"],
            Bill.bill_date >= from_date,
            Bill.bill_date <= to_date,
            Bill.status == "posted",
        )
    )).all()
    aggregates: dict[str, dict[str, Decimal]] = {"product": {}, "brand": {}, "category": {}}
    for item, product, brand, category in lines:
        for dimension, name in (
            ("product", product.name),
            ("brand", brand.name if brand else "Unbranded"),
            ("category", category.name if category else "Uncategorized"),
        ):
            aggregates[dimension][name] = aggregates[dimension].get(name, ZERO) + item.line_total
    by_day_items = [{"date": key, "sales": f"{amount:.2f}"} for key, amount in sorted(by_day.items())]
    if format == "xlsx":
        return _xlsx_response("Sales", ["Date", "Sales"], [[row["date"], row["sales"]] for row in by_day_items], "sales-report.xlsx")
    return {
        "from": from_date.isoformat(),
        "to": to_date.isoformat(),
        "byDay": by_day_items,
        "byProduct": [{"name": key, "sales": f"{value:.2f}"} for key, value in aggregates["product"].items()],
        "byBrand": [{"name": key, "sales": f"{value:.2f}"} for key, value in aggregates["brand"].items()],
        "byCategory": [{"name": key, "sales": f"{value:.2f}"} for key, value in aggregates["category"].items()],
        "total": f"{sum((bill.total for bill in bills), ZERO):.2f}",
    }


@router.get("/reports/dues")
async def report_dues(
    format: str | None = Query(None, pattern="^(xlsx)$"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=100),
    q: str | None = None,
    sort: str = "outstanding:desc",
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    data = await khata_dues(page=page, pageSize=pageSize, q=q, sort=sort, db=db, identity=identity)
    if format == "xlsx":
        return _xlsx_response(
            "Dues", ["Farmer", "Mobile", "Outstanding", "Overdue days", "Last payment"],
            [[row["name"], row["mobile"], row["outstanding"], row["overdueDays"], row["lastPaymentDate"]] for row in data["items"]],
            "dues-report.xlsx",
        )
    return data


@router.get("/reports/profit")
async def report_profit(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    format: str | None = Query(None, pattern="^(xlsx)$"),
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    bills = (await db.execute(select(Bill).where(
        Bill.tenant_id == identity["tenant_id"], Bill.bill_date >= from_date,
        Bill.bill_date <= to_date, Bill.status == "posted"
    ))).scalars().all()
    revenue = sum((bill.total for bill in bills), ZERO)
    cost = ZERO
    bill_ids = [bill.id for bill in bills]
    if bill_ids:
        sold_lines = (await db.execute(select(BillItem, Pack).join(
            Pack, (Pack.id == BillItem.pack_id) & (Pack.tenant_id == BillItem.tenant_id)
        ).where(
            BillItem.tenant_id == identity["tenant_id"], BillItem.bill_id.in_(bill_ids)
        ))).all()
        for item, pack in sold_lines:
            lots = (await db.execute(select(StockLot).where(
                StockLot.tenant_id == identity["tenant_id"], StockLot.pack_id == pack.id
            ))).scalars().all()
            received = sum((lot.quantity_base for lot in lots), ZERO)
            if received:
                weighted_cost_per_base = sum(
                    (lot.quantity_base * lot.cost_price / pack.size_in_base_unit for lot in lots), ZERO
                ) / received
                cost += item.quantity_base * weighted_cost_per_base
    data = {
        "revenue": f"{revenue:.2f}",
        "interestEarned": f"{sum((bill.interest_amount for bill in bills), ZERO):.2f}",
        "cost": f"{cost:.2f}",
        "profit": f"{(revenue - cost):.2f}",
    }
    if format == "xlsx":
        return _xlsx_response("Profit", ["Revenue", "Interest earned", "Cost", "Profit"], [[data["revenue"], data["interestEarned"], data["cost"], data["profit"]]], "profit-report.xlsx")
    return data


@router.get("/reports/stock-valuation")
async def report_stock_valuation(
    format: str | None = Query(None, pattern="^(xlsx)$"),
    db: AsyncSession = Depends(get_db),
    identity: dict[str, uuid.UUID] = Depends(current_identity),
):
    packs = (await db.execute(select(Pack).where(
        Pack.tenant_id == identity["tenant_id"], Pack.active.is_(True)
    ))).scalars().all()
    at_mrp = ZERO
    at_cost = ZERO
    quantities = []
    for pack in packs:
        balance = Decimal(str(await db.scalar(select(func.coalesce(func.sum(StockMovement.quantity_base), 0)).where(
            StockMovement.tenant_id == identity["tenant_id"], StockMovement.pack_id == pack.id
        )) or 0))
        pack_count = balance / pack.size_in_base_unit
        at_mrp += pack_count * pack.mrp
        lots = (await db.execute(select(StockLot).where(
            StockLot.tenant_id == identity["tenant_id"], StockLot.pack_id == pack.id
        ))).scalars().all()
        received = sum((lot.quantity_base for lot in lots), ZERO)
        cost_value = ZERO
        if received:
            weighted_cost_per_base = sum(
                (lot.quantity_base * lot.cost_price / pack.size_in_base_unit for lot in lots), ZERO
            ) / received
            cost_value = balance * weighted_cost_per_base
        at_cost += cost_value
        quantities.append((pack, pack_count, cost_value))
    items = [{"packId": str(pack.id), "quantityPacks": str(count), "mrpValue": f"{count * pack.mrp:.2f}", "costValue": f"{cost_value:.2f}"} for pack, count, cost_value in quantities]
    if format == "xlsx":
        return _xlsx_response("Stock valuation", ["Pack ID", "Quantity packs", "MRP value", "Cost value"], [[row["packId"], row["quantityPacks"], row["mrpValue"], row["costValue"]] for row in items], "stock-valuation.xlsx")
    return {"atMrp": f"{at_mrp:.2f}", "atCost": f"{at_cost:.2f}", "items": items}

