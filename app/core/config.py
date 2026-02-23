from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Database GMT"
    VERSION: str = "1.0.0"
    # Prefer setting DATABASE_URL and SECRET_KEY in .env for production
    DATABASE_URL: str = "postgresql://postgres:GMTrangkas1207@localhost/dbgmt"
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # default untuk user biasa

    model_config = ConfigDict(env_file=".env")
    mdb_path: str = "Q:\\att2026.mdb"

settings = Settings()