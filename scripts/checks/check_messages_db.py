from sqlmodel import Session, select
from app.database import engine
from app.models import Message

def check_messages():
    with Session(engine) as session:
        stmt = select(Message).where(Message.contact_id == 1).order_by(Message.created_at.desc()).limit(5)
        msgs = session.exec(stmt).all()
        print(f"Messages for Contact 1 (Phone):")
        for m in msgs:
            print(f"[{m.role}] {m.content}")

if __name__ == "__main__":
    check_messages()
