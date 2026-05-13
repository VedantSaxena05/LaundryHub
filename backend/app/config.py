from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Dict, List

HOSTEL_BLOCKS = ["A", "B", "C", "D", "E"]
DEFAULT_BLOCK_SLOT_LIMIT = 30
DROPOFF_START_HOUR    = 10
DROPOFF_END_HOUR      = 19
COLLECTION_START_HOUR = 11
COLLECTION_END_HOUR   = 19


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    FIREBASE_CREDENTIALS_PATH: str = "firebase-credentials.json"
    BLOCK_SLOT_LIMITS: Dict[str, int] = {}
    MONTHLY_SLOT_QUOTA_PER_STUDENT: int = 4
    APP_ENV: str = "development"

    # Store as plain string, parse manually — avoids pydantic-settings JSON parsing
    CORS_ORIGINS: str = "*"

    def get_cors_origins(self) -> List[str]:
        v = self.CORS_ORIGINS.strip()
        if not v or v == "*":
            return ["*"]
        return [o.strip() for o in v.split(",") if o.strip()]

    def get_block_limit(self, block: str) -> int:
        return self.BLOCK_SLOT_LIMITS.get(block.upper(), DEFAULT_BLOCK_SLOT_LIMIT)

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()