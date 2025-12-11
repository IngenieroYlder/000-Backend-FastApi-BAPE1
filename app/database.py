from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

SQL_ALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace("%", "%%") # Escape básico si es necesario, aunque psycopg2 maneja la mayoría

# Para versiones más nuevas de SQLAlchemy, considera usar el objeto URL, pero string está bien por ahora según requisitos
engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
