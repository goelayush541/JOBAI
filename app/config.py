from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "JobTrackerAI"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-to-a-random-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/jobtracker"

    GCP_PROJECT_ID: str = ""
    GCP_REGION: str = "us-central1"
    GCS_BUCKET_NAME: str = "jobtracker-resumes"

    VERTEX_AI_MODEL: str = "gemini-1.5-pro"

    CLOUD_TASKS_QUEUE: str = "job-tracker-queue"
    CLOUD_TASKS_LOCATION: str = "us-central1"

    ENCRYPTION_ENABLED: bool = True
    ENCRYPTION_KEY: str = "local-dev-encryption-key-change-in-production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
