from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

# SQLModel uses SQLAlchemy under the hood, so create_engine works the same
engine = create_engine(settings.DATABASE_URL)

def get_db():
    with Session(engine) as session:
        yield session

get_session = get_db
