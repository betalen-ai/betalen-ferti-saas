import httpx


class EmailClient:
    def __init__(self, base_url: str, service_key: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.service_key = service_key
        self.timeout = timeout

    async def send(self, *, template: str, to_email: str, to_name: str | None,
                   tenant_id: str | None, user_id: str | None, expires_at=None,
                   idempotency_key: str, priority: str = "NORMAL", data: dict,
                   request_id: str | None = None) -> dict | None:
        headers = {
            "X-Service-Key": self.service_key,
            "Idempotency-Key": idempotency_key,
        }
        if request_id:
            headers["X-Request-Id"] = request_id
        payload = {
            "template": template,
            "to": {"email": to_email, "name": to_name},
            "tenantId": tenant_id,
            "userId": user_id,
            "priority": priority,
            "expiresAt": expires_at,
            "data": data,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(3):
                try:
                    response = await client.post(
                        f"{self.base_url}/v1/emails",
                        headers=headers,
                        json=payload,
                    )
                    if response.status_code in (202, 409):
                        return response.json()
                    response.raise_for_status()
                except httpx.HTTPError:
                    if attempt == 2:
                        return None
        return None
