from sqlmodel import Session, select, create_engine
from app.models import CompanySettings
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
engine = create_engine(DATABASE_URL)

with Session(engine) as session:
    settings = session.exec(select(CompanySettings).where(CompanySettings.company_id == 1)).first()
    if settings:
        print(f"OpenAI Key: {'Hidden' if settings.openai_api_key else 'None'}")
    else:
        print("No settings found for company 1")
