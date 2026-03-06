from app.database import engine
from sqlalchemy import text
from sqlmodel import Session

def check_pgvector():
    with Session(engine) as session:
        try:
            # Try to create extension if not exists
            session.exec(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            session.commit()
            print("SUCCESS: pgvector extension enabled!")
            return True
        except Exception as e:
            print(f"FAILURE: Could not enable pgvector. Error: {e}")
            return False

if __name__ == "__main__":
    check_pgvector()
