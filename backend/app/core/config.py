from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_secret_key: str = "dev-secret-key"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # DB
    database_url: str = "sqlite+aiosqlite:///./jobhunt.db"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # Scraping
    scraper_max_workers: int = 6
    scraper_rate_limit_delay: float = 2.0
    scraper_max_results_per_board: int = 25
    default_location: str = "Canada"

    # Uploads
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
