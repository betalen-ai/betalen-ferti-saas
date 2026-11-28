from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENVIRONMENT: str = "local"
    
    DATABASE_URL: str = "postgresql+asyncpg://betalen:betalen_dev_pw@postgres:5432/betalen_db"
    JWT_SECRET: str = "change_me_in_prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 120

    # Service Routing URLs
    ORG_SERVICE_URL: str = "http://beta_organization:8001"
    BILLING_SERVICE_URL: str = "http://beta_billing:8002"
    INVENTORY_SERVICE_URL: str = "http://beta_inventory:8003"
    REPORTS_SERVICE_URL: str = "http://beta_reports:8004"

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
