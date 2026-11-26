# beta_email

Internal transactional email service for Ferti+. It exposes no public routes and runs on port 8005 in the Docker network.

## Providers

- `console`: print email subjects (local default)
- `mailpit`: SMTP delivery to `mailpit:1025`
- `gmail_smtp`: Gmail STARTTLS with `GMAIL_USER` and `GMAIL_APP_PASSWORD`

Set `ENCRYPTION_KEY` to a stable 32-byte value. Calls require `X-Service-Key`, `X-Request-Id`, and `Idempotency-Key`.

## Development

```powershell
docker compose up postgres mailpit beta_email
```

Open Mailpit at http://localhost:8025.
