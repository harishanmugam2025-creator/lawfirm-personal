from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = "veritas-dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DEBUG_MODE: bool = False
    
    # DATABASE_URL: str = "sqlite:///./veritas.db"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/veritas"
    
    OPA_URL: str = "http://localhost:8181"
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_API_KEY: str | None = None
    
    # SendGrid Settings
    SENDGRID_API_KEY: str = "SG.placeholder"
    SENDGRID_FROM_EMAIL: str = "ravanthsri20@gmail.com"
    SENDGRID_FROM_NAME: str = "Veritas AI"

    # MinIO / S3 Settings
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "lawfirm-documents"

    model_config = ConfigDict(env_file=".env")


settings = Settings()
