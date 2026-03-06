import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_ROOT = BASE_DIR
    VAR_DIR = PROJECT_ROOT / "var"
    LOG_DIR = VAR_DIR / "logs"
    DATA_DIR = VAR_DIR / "data"
    CALENDAR_DEBUG_LOG = LOG_DIR / "calendar_debug.log"
    WEBHOOK_DEBUG_LOG = LOG_DIR / "webhook_debug.log"
    EMERGENCY_SESSIONS_FILE = DATA_DIR / "emergency_sessions.json"

    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "n8n_bape")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "BAPE_BD")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "BAPE")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "Ne2Obp5WBp4-FWnr4g\\")
    
    SECRET_KEY = os.getenv("SECRET_KEY", "your_super_secret_key_change_this_in_production")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    # AI Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    @property
    def DATABASE_URL(self):
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Email Settings
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL") # Optional, defaults to user

    # Scheduler Settings
    REMINDER_HOURS_BEFORE = int(os.getenv("REMINDER_HOURS_BEFORE", 1))

settings = Settings()
settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
BAILEYS_ENGINE_URL = "http://127.0.0.1:3005"
