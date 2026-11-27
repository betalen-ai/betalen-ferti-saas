"""All ferti routes. Mount with: app.include_router(router, prefix="/ferti")"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import CurrentUser, get_current_user, resolve_tenant_id
from app.models.ferti import (
    AuditLog, Bill, BillItem, Brand, CashbookEntry, Category, Farmer, KhataEntry,
    Pack, Payment, Product, Season, Setting, StockLot, StockMovement,
)
from app.routes.ferti_crud import (
    build_crud_router, commit_or_conflict, ensure_same_tenant, get_owned,
    not_found, resolve_request_tenant,
)
from app.schemas.ferti import (
    AuditLogOut, BrandCreate, BrandOut, BrandUpdate, BillItemOut, BillOut, CashbookCreate, CashbookOut, CashbookUpdate,
    CategoryCreate, CategoryOut, CategoryUpdate, FarmerCreate, FarmerOut, FarmerUpdate,
    KhataEntryOut, PackCreate, PackOut, PackUpdate, PaymentOut, ProductCreate,
    ProductOut, ProductUpdate, SeasonCreate, SeasonOut, SeasonUpdate, SettingsIn,
    SettingsOut, StockLotCreate, StockLotOut, StockLotUpdate, StockMovementCreate,
    StockMovementOut,
)

router = APIRouter()

# ---------------- simple tenant-scoped masters ----------------
router.include_router(build_crud_router(
    prefix="/brands", tag="brands", model=Brand,
    create_schema=BrandCreate, update_schema=BrandUpdate, out_schema=BrandOut,
    not_found_detail="brand_not_found", conflict_detail="brand_name_already_exists",
    order_by=[Brand.name], search_columns=[Brand.name, Brand.manufacturer], soft_delete=True,
))
router.include_router(build_crud_router(
    prefix="/categories", tag="categories", model=Category,
    create_schema=CategoryCreate, update_schema=CategoryUpdate, out_schema=CategoryOut,
    not_found_detail="category_not_found", conflict_detail="category_name_already_exists",
    order_by=[Category.name], search_columns=[Category.name], soft_delete=True,
))
router.include_router(build_crud_router(
    prefix="/products", tag="products", model=Product,
    create_schema=ProductCreate, update_schema=ProductUpdate, out_schema=ProductOut,
    not_found_detail="product_not_found", conflict_detail="product_already_exists",
    order_by=[Product.name], search_columns=[Product.name, Product.hsn],
    fk_checks={"brand_id": Brand, "category_id": Category}, soft_delete=True,
))
router.include_router(build_crud_router(
    prefix="/packs", tag="packs", model=Pack,
    create_schema=PackCreate, update_schema=PackUpdate, out_schema=PackOut,
    not_found_detail="pack_not_found", conflict_detail="pack_size_or_barcode_already_exists",
    order_by=[Pack.created_at.desc()], search_columns=[Pack.barcode],
    fk_checks={"product_id": Product}, soft_delete=True,
))
router.include_router(build_crud_router(
    prefix="/farmers", tag="farmers", model=Farmer,
    create_schema=FarmerCreate, update_schema=FarmerUpdate, out_schema=FarmerOut,
    not_found_detail="farmer_not_found", conflict_detail="farmer_mobile_already_exists",
    order_by=[Farmer.name], search_columns=[Farmer.name, Farmer.mobile, Farmer.village],
    soft_delete=True,
))
router.include_router(build_crud_router(
    prefix="/seasons", tag="seasons", model=Season,
    create_schema=SeasonCreate, update_schema=SeasonUpdate, out_schema=SeasonOut,
    not_found_detail="season_not_found", conflict_detail="season_name_already_exists",
    order_by=[Season.start_date.desc()], search_columns=[Season.name],
))
router.include_router(build_crud_router(
    prefix="/cashbook", tag="cashbook", model=CashbookEntry,
    create_schema=CashbookCreate, update_schema=CashbookUpdate, out_schema=CashbookOut,
    not_found_detail="cashbook_entry_not_found", conflict_detail="cashbook_conflict",
    order_by=[CashbookEntry.entry_date.desc(), CashbookEntry.created_at.desc()],
    search_columns=[CashbookEntry.category],
))

# ---------------- read-only ledgers (written by billing/payment services) ----------------
router.include_router(build_crud_router(
    prefix="/bills", tag="bills", model=Bill,
    create_schema=None, update_schema=None, out_schema=BillOut,
    not_found_detail="bill_not_found", conflict_detail="bill_conflict",
    order_by=[Bill.bill_date.desc(), Bill.created_at.desc()], search_columns=[Bill.bill_number],
    fk_checks={"farmer_id": Farmer, "season_id": Season}, writable=False,
))
router.include_router(build_crud_router(
    prefix="/payments", tag="payments", model=Payment,
    create_schema=None, update_schema=None, out_schema=PaymentOut,
    not_found_detail="payment_not_found", conflict_detail="payment_conflict",
    order_by=[Payment.payment_date.desc(), Payment.created_at.desc()],
    fk_checks={"farmer_id": Farmer, "bill_id": Bill}, writable=False,
))
router.include_router(build_crud_router(
    prefix="/khata", tag="khata", model=KhataEntry,
    create_schema=None, update_schema=None, out_schema=KhataEntryOut,
    not_found_detail="khata_entry_not_found", conflict_detail="khata_conflict",
    order_by=[KhataEntry.created_at.desc()],
    fk_checks={"farmer_id": Farmer, "bill_id": Bill}, writable=False,
))
router.include_router(build_crud_router(
    prefix="/audit-logs", tag="audit", model=AuditLog,
    create_schema=None, update_schema=None, out_schema=AuditLogOut,
    not_found_detail="audit_log_not_found", conflict_detail="audit_conflict",
    order_by=[AuditLog.created_at.desc()], writable=False,
))

bill_items = APIRouter(prefix="/bills", tags=["bills"])


@bill_items.get("/{bill_id}/items", response_model=list[BillItemOut])
async def list_bill_items(
    bill_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_tenant_id(cu, tenant_id)
    await get_owned(db, Bill, bill_id, owned, "bill_not_found")
    result = await db.execute(
        select(BillItem).where(BillItem.bill_id == bill_id, BillItem.tenant_id == owned)
        .order_by(BillItem.created_at)
    )
    return result.scalars().all()


router.include_router(bill_items)

# ---------------- stock lots (create also writes a "receipt" movement) ----------------
lots = APIRouter(prefix="/stock-lots", tags=["stock"])


@lots.get("", response_model=list[StockLotOut])
async def list_lots(
    tenant_id: uuid.UUID | None = Query(default=None),
    pack_id: uuid.UUID | None = None,
    in_stock_only: bool = False,
    expiring_before: date | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_tenant_id(cu, tenant_id)
    query = select(StockLot).where(StockLot.tenant_id == owned)
    if pack_id:
        query = query.where(StockLot.pack_id == pack_id)
    if in_stock_only:
        query = query.where(StockLot.available_base > 0)
    if expiring_before:
        query = query.where(StockLot.expiry_date.is_not(None), StockLot.expiry_date <= expiring_before)
    result = await db.execute(
        query.order_by(StockLot.expiry_date.asc().nulls_last(), StockLot.received_date).limit(limit).offset(offset)
    )
    return result.scalars().all()


@lots.post("", response_model=StockLotOut, status_code=status.HTTP_201_CREATED)
async def create_lot(
    payload: StockLotCreate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    await ensure_same_tenant(db, Pack, payload.pack_id, owned, "pack_id")
    lot = StockLot(
        tenant_id=owned,
        available_base=payload.quantity_base,
        **payload.model_dump(exclude={"tenant_id"}),
    )
    db.add(lot)
    await db.flush()
    db.add(StockMovement(
        tenant_id=owned, pack_id=lot.pack_id, stock_lot_id=lot.id,
        movement_type="receipt", quantity_base=lot.quantity_base,
        source_id=lot.id, source_type="stock_lot",
    ))
    await commit_or_conflict(db, "stock_lot_conflict")
    await db.refresh(lot)
    return lot


@lots.get("/{lot_id}", response_model=StockLotOut)
async def get_lot(
    lot_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_owned(db, StockLot, lot_id, resolve_tenant_id(cu, tenant_id), "stock_lot_not_found")


@lots.patch("/{lot_id}", response_model=StockLotOut)
async def update_lot(
    lot_id: uuid.UUID,
    payload: StockLotUpdate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    lot = await get_owned(db, StockLot, lot_id, owned, "stock_lot_not_found")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True, exclude={"tenant_id"}).items():
        setattr(lot, field, value)
    lot.version += 1
    await commit_or_conflict(db, "stock_lot_conflict")
    await db.refresh(lot)
    return lot


router.include_router(lots)

# ---------------- stock movements (manual adjustments change lot.available_base) ----------------
movements = APIRouter(prefix="/stock-movements", tags=["stock"])


@movements.get("", response_model=list[StockMovementOut])
async def list_movements(
    tenant_id: uuid.UUID | None = Query(default=None),
    pack_id: uuid.UUID | None = None,
    stock_lot_id: uuid.UUID | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_tenant_id(cu, tenant_id)
    query = select(StockMovement).where(StockMovement.tenant_id == owned)
    if pack_id:
        query = query.where(StockMovement.pack_id == pack_id)
    if stock_lot_id:
        query = query.where(StockMovement.stock_lot_id == stock_lot_id)
    result = await db.execute(query.order_by(StockMovement.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()


@movements.get("/{movement_id}", response_model=StockMovementOut)
async def get_movement(
    movement_id: uuid.UUID,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_owned(db, StockMovement, movement_id, resolve_tenant_id(cu, tenant_id), "stock_movement_not_found")


@movements.post("", response_model=StockMovementOut, status_code=status.HTTP_201_CREATED)
async def create_movement(
    payload: StockMovementCreate,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    result = await db.execute(
        select(StockLot)
        .where(StockLot.id == payload.stock_lot_id, StockLot.tenant_id == owned)
        .with_for_update()
    )
    lot = result.scalar_one_or_none()
    if lot is None:
        raise not_found("stock_lot_not_found")
    new_available = lot.available_base + payload.quantity_base
    if new_available < 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="insufficient_stock")
    lot.available_base = new_available
    lot.version += 1
    movement = StockMovement(
        tenant_id=owned, pack_id=lot.pack_id, stock_lot_id=lot.id,
        movement_type=payload.movement_type, quantity_base=payload.quantity_base,
        reason=payload.reason, source_type="manual",
    )
    db.add(movement)
    await commit_or_conflict(db, "stock_movement_conflict")
    await db.refresh(movement)
    return movement


router.include_router(movements)

# ---------------- settings (one row per tenant) ----------------
settings = APIRouter(prefix="/settings", tags=["settings"])


@settings.get("", response_model=SettingsOut)
async def get_settings(
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_tenant_id(cu, tenant_id)
    row = await db.get(Setting, owned)
    if row is None:
        raise not_found("settings_not_found")
    return row


@settings.put("", response_model=SettingsOut)
async def put_settings(
    payload: SettingsIn,
    tenant_id: uuid.UUID | None = Query(default=None),
    cu: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned = resolve_request_tenant(cu, tenant_id, payload.tenant_id)
    row = await db.get(Setting, owned)
    if row is None:
        row = Setting(tenant_id=owned, values=payload.values)
        db.add(row)
    else:
        row.values = payload.values
    await commit_or_conflict(db, "settings_conflict")
    await db.refresh(row)
    return row


router.include_router(settings)
