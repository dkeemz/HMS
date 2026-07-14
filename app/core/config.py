
from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "HMS"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://hms:hms_dev@localhost:5432/hms"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    KEYCLOAK_SERVER_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "hms"
    KEYCLOAK_CLIENT_ID: str = "hms-backend"
    KEYCLOAK_CLIENT_SECRET: str = "change-me"

    ELASTICSEARCH_URL: str = "http://localhost:9200"

    CORS_ORIGINS: list[str] = ["http://localhost:8000"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    @model_validator(mode="after")
    def _reject_default_secrets(self) -> "Settings":
        if not self.DEBUG:
            unsafe_defaults = {
                "SECRET_KEY": self.SECRET_KEY,
                "KEYCLOAK_CLIENT_SECRET": self.KEYCLOAK_CLIENT_SECRET,
            }
            for field, value in unsafe_defaults.items():
                if "change-me" in value:
                    raise ValueError(
                        f"{field} still contains a placeholder value. "
                        f"Set a real value in .env when DEBUG=False."
                    )
        return self


settings = Settings()
