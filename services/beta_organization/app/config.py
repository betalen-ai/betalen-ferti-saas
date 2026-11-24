from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://betalen:betalen_dev_pw@postgres:5432/betalen_db"
    JWT_SECRET: str = "change_me_in_prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 120

    class Config:
        env_file = ".env"

settings = Settings()
