from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = "development"
    EMAIL_PROVIDER: str = "console"
    GMAIL_SMTP_HOST: str = "smtp.gmail.com"
    GMAIL_SMTP_PORT: int = 587
    GMAIL_USER: str = ""
    GMAIL_APP_PASSWORD: str = ""
    MAIL_FROM_NAME: str = "Ferti+"
    MAIL_FROM_ADDRESS: str = "noreply@ferti.example"
    MAIL_REPLY_TO: str = "support@ferti.example"
    SUPPORT_EMAIL: str = "support@ferti.example"
    APP_BASE_URL: str = "https://app.ferti.example"
    DATABASE_URL: str = "postgresql+asyncpg://betalen:betalen_dev_pw@postgres:5432/betalen_db"
    ENCRYPTION_KEY: str = "change_this_32_byte_encryption_key"
    SERVICE_API_KEYS: str = ""
    ADMIN_API_KEY: str = ""
    DAILY_SEND_LIMIT: int = 400
    WORKER_POLL_SECONDS: float = 2
    WORKER_BATCH_SIZE: int = 10
    MAX_ATTEMPTS: int = 5
    MAILPIT_HOST: str = "mailpit"
    MAILPIT_PORT: int = 1025
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
