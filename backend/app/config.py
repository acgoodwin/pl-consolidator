import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://app:devpass@localhost:5432/pl_consolidator"
    )
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    upload_folder: str = os.getenv("UPLOAD_FOLDER", "/tmp/pl-consolidator-uploads")
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    cors_origins: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
