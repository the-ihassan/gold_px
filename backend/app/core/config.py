"""
Central application configuration.
All values are read from environment variables (see .env.example).
Nothing here should ever hold real secrets.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    # ---- General ----
    PROJECT_NAME: str = "GOLD Px Backend"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True

    # ---- Security / JWT ----
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ---- Database ----
    POSTGRES_USER: str = "goldpx"
    POSTGRES_PASSWORD: str = "goldpx"
    POSTGRES_DB: str = "goldpx"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v, info):
        if v:
            return v
        data = info.data
        return (
            f"postgresql+psycopg2://{data.get('POSTGRES_USER')}:"
            f"{data.get('POSTGRES_PASSWORD')}@{data.get('POSTGRES_HOST')}:"
            f"{data.get('POSTGRES_PORT')}/{data.get('POSTGRES_DB')}"
        )

    # ---- Redis / Celery ----
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def assemble_broker(cls, v, info):
        if v:
            return v
        data = info.data
        return f"redis://{data.get('REDIS_HOST')}:{data.get('REDIS_PORT')}/0"

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_backend(cls, v, info):
        if v:
            return v
        data = info.data
        return f"redis://{data.get('REDIS_HOST')}:{data.get('REDIS_PORT')}/1"

    # ---- CORS ----
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # ---- File storage ----
    # STORAGE_BACKEND: "local" now; switch to "cloudinary" or "s3" later
    # without touching any endpoint code (see app/services/storage_service.py).
    STORAGE_BACKEND: str = "local"
    LOCAL_UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 15

    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None

    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_REGION: Optional[str] = None

    # ---- Notifications ----
    # WhatsApp: no Business API key yet -> we generate wa.me deep links
    # that staff/admin click to message the customer directly.
    WHATSAPP_BUSINESS_NUMBER: str = "923145355656"

    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "no-reply@goldpx.com"
    SMTP_FROM_NAME: str = "GOLD Px"

    # SMS provider (Twilio etc.) - placeholder until keys are supplied
    SMS_PROVIDER_ENABLED: bool = False
    SMS_API_KEY: Optional[str] = None
    SMS_API_SECRET: Optional[str] = None

    # ---- Rate limiting ----
    RATE_LIMIT_PER_MINUTE: int = 60

    # ---- First super admin (seed) ----
    FIRST_SUPERADMIN_EMAIL: str = "admin@goldpx.com"
    FIRST_SUPERADMIN_PASSWORD: str = "ChangeMe123!"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
