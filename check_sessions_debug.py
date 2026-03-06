from sqlmodel import Session, select, create_engine
from app.models import WhatsAppSession
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
engine = create_engine(DATABASE_URL)

with Session(engine) as session:
    sessions = session.exec(select(WhatsAppSession)).all()
    for s in sessions:
        print(f"ID: {s.id}, Name: {s.session_name}, Alias: {s.alias}, Status: {s.status}")
