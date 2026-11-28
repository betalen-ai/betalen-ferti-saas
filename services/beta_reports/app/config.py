from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://betalen:betalen_dev_pw@postgres:5432/betalen_db"
    JWT_SECRET: str = "change_me_in_prod"
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()