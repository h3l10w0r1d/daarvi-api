from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/daarvi"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Replicate API token for virtual try-on (IDM-VTON model)
    # Get yours at https://replicate.com/account/api-tokens
    REPLICATE_API_TOKEN: str = ""

    # Comma-separated list of allowed CORS origins.
    # In production set to your Vercel URL, e.g.:
    #   https://your-app.vercel.app,https://www.your-domain.com
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def database_url_async(self) -> str:
        """
        Render Postgres gives a connection string starting with 'postgres://'
        or 'postgresql://'. asyncpg requires 'postgresql+asyncpg://'.
        This converts either format automatically.
        """
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            return "postgresql+asyncpg://" + url[len("postgres://"):]
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            return "postgresql+asyncpg://" + url[len("postgresql://"):]
        return url

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
