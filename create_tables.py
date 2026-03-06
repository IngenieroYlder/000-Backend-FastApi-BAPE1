from sqlmodel import SQLModel
from app.database import engine
from app.models import * # Import all models to register them

def create_tables():
    print("Creating tables...")
    SQLModel.metadata.create_all(engine)
    print("Tables created.")

if __name__ == "__main__":
    create_tables()
