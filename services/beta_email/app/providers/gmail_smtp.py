import aiosmtplib
from email.message import EmailMessage as MimeEmail

from app.config import settings
from app.providers.base import EmailProvider, ProviderResult


class SmtpProvider(EmailProvider):
    def __init__(self, host: str, port: int, username: str = "", password: str = "", use_tls: bool = False):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.name = "gmail_smtp"

    async def send(self, message: MimeEmail) -> ProviderResult:
        try:
            response = await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.username or None,
                password=self.password or None,
                start_tls=not self.use_tls and bool(self.username),
                use_tls=self.use_tls,
                timeout=20,
            )
            return ProviderResult(ok=True, provider_message_id=getattr(message, "get", lambda *_: None)("Message-ID"))
        except aiosmtplib.SMTPException as exc:
            code = getattr(exc, "code", None)
            return ProviderResult(
                ok=False,
                temporary=code is None or 400 <= int(code) < 500,
                smtp_code=int(code) if isinstance(code, int) else None,
                error=str(exc).replace(settings.GMAIL_APP_PASSWORD, "***") if settings.GMAIL_APP_PASSWORD else str(exc),
            )
        except Exception as exc:
            return ProviderResult(ok=False, temporary=True, error=type(exc).__name__)


class GmailSmtpProvider(SmtpProvider):
    def __init__(self):
        super().__init__(
            settings.GMAIL_SMTP_HOST,
            settings.GMAIL_SMTP_PORT,
            settings.GMAIL_USER,
            settings.GMAIL_APP_PASSWORD,
        )
        self.name = "gmail_smtp"
