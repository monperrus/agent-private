from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://journal:journal@db:5432/journal"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    UPLOAD_DIR: str = "/uploads"
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

settings = Settings()
