import uuid
from typing import Any

from app.schemas.common import RecordOut


class AuditLogOut(RecordOut):
    user_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    action: str
    old_values: dict[str, Any] | None
    new_values: dict[str, Any] | None