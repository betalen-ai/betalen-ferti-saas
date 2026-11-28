from email.message import EmailMessage as MimeEmail

from app.providers.base import EmailProvider, ProviderResult


class ConsoleProvider(EmailProvider):
    name = "console"

    async def send(self, message: MimeEmail) -> ProviderResult:
        print(f"[EMAIL:{message['To']}] {message['Subject']}")
        return ProviderResult(ok=True, provider_message_id="console://sent")
