from sqlmodel import Session, select, create_engine
from app.models import Message, WhatsAppSession, Contact
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

def check_messages():
    with Session(engine) as session:
        # Check Sessions
        wa_sessions = session.exec(select(WhatsAppSession)).all()
        print(f"--- SESSIONS ({len(wa_sessions)}) ---")
        for s in wa_sessions:
            print(f"ID: {s.id} | Name: {s.session_name} | Alias: {s.alias} | Status: {s.status}")

        # Check Messages
        messages = session.exec(select(Message).order_by(Message.id.desc()).limit(5)).all()
        print(f"\n--- LAST 5 MESSAGES ---")
        for m in messages:
            print(f"ID: {m.id} | Content: {m.content} | Sender: {m.sender_name} | SessionID: {m.session_id}")

if __name__ == "__main__":
    check_messages()
