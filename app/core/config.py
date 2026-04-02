from __future__ import annotations

from functools import lru_cache

from pydantic import EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Finance Dashboard API"
    environment: str = "development"
    database_url: str = Field(..., validation_alias="DATABASE_URL")
    jwt_secret: str = Field(..., validation_alias="JWT_SECRET")
    jwt_expire_minutes: int = Field(60, validation_alias="JWT_EXPIRE_MINUTES")
    auth_rate_limit_requests: int = Field(5, validation_alias="AUTH_RATE_LIMIT_REQUESTS")
    auth_rate_limit_window_seconds: int = Field(60, validation_alias="AUTH_RATE_LIMIT_WINDOW_SECONDS")
    admin_email: EmailStr = Field(..., validation_alias="ADMIN_EMAIL")
    admin_password: str = Field(..., validation_alias="ADMIN_PASSWORD")
    docs_url: str = "/docs"
    redoc_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if len(value) < 16:
            raise ValueError("JWT_SECRET must be at least 16 characters long.")
        return value

    @field_validator("jwt_expire_minutes")
    @classmethod
    def validate_expiration(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("JWT_EXPIRE_MINUTES must be greater than 0.")
        return value

    @field_validator("auth_rate_limit_requests", "auth_rate_limit_window_seconds")
    @classmethod
    def validate_rate_limit_values(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Rate limit settings must be greater than 0.")
        return value

    @field_validator("admin_password")
    @classmethod
    def validate_admin_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("ADMIN_PASSWORD must be at least 8 characters long.")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
