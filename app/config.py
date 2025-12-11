import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "n8n_bape")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "BAPE_BD")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "BAPE")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "Ne2Obp5WBp4-FWnr4g\\")
    
    SECRET_KEY = os.getenv("SECRET_KEY", "your_super_secret_key_change_this_in_production")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    @property
    def DATABASE_URL(self):
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()