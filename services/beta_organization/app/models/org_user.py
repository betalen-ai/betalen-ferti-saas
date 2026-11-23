import uuid
from datetime import datetime

from sqlalchemy import Boolean, String, DateTime, ForeignKey, UniqueConstraint, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class OrgUser(Base):
    __tablename__ = "org_users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_org_user_email"),
        UniqueConstraint("tenant_id", "phone", name="uq_org_user_tenant_phone"),
        {"schema": "org"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org.tenants.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(24))
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    phone_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en", server_default="en")
    role_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("org.roles.id"))
    status: Mapped[str] = mapped_column(String, default="active")
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())