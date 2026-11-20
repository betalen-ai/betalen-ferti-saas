from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://betalen:betalen_dev_pw@postgres:5432/betalen_db"
    JWT_SECRET: str = "change_me_in_prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 120
    ENVIRONMENT: str = "development"
    PUBLIC_API_URL: str = "http://localhost:8000"
    OTP_PROVIDER_URL: str | None = None
    OTP_PROVIDER_API_KEY: str | None = None
    EMAIL_PROVIDER_URL: str | None = None
    EMAIL_PROVIDER_API_KEY: str | None = None
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None
    FRONTEND_URL: str = "http://localhost:4200"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
