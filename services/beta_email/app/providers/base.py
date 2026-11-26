from dataclasses import dataclass
from email.message import EmailMessage as MimeEmail


@dataclass
class ProviderResult:
    ok: bool
    temporary: bool = False
    provider_message_id: str | None = None
    smtp_code: int | None = None
    error: str | None = None


class EmailProvider:
    name = "base"

    async def send(self, message: MimeEmail) -> ProviderResult:
        raise NotImplementedError
