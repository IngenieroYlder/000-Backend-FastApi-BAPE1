from sqlmodel import Session, select, delete
from app.database import engine
from app.models import WhatsAppSession

def clean_sessions():
    with Session(engine) as session:
        statement = delete(WhatsAppSession)
        result = session.exec(statement)
        session.commit()
        print(f"Deleted {result.rowcount} stale sessions.")

if __name__ == "__main__":
    clean_sessions()
