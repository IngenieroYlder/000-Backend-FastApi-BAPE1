from sqlmodel import Session, select
from app.database import engine
from app.models import WhatsAppSession

def set_groq():
    with Session(engine) as session:
        stmt = select(WhatsAppSession).where(WhatsAppSession.session_name == "company_1_andrew")
        wa_session = session.exec(stmt).first()
        if wa_session:
            wa_session.ai_provider = "groq"
            session.add(wa_session)
            session.commit()
            print("Changed andrew session provider to groq.")
        else:
            print("Session andrew not found.")

if __name__ == "__main__":
    set_groq()
