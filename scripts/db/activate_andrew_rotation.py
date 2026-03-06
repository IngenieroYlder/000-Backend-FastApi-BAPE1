from sqlmodel import Session, select
from app.database import engine
from app.models import WhatsAppSession

def activate_rotation():
    with Session(engine) as session:
        stmt = select(WhatsAppSession).where(WhatsAppSession.session_name == "company_1_andrew")
        wa_session = session.exec(stmt).first()
        if wa_session:
            wa_session.ai_strategy = "rotate_free"
            session.add(wa_session)
            session.commit()
            print("Activated rotate_free strategy for andrew.")
        else:
            print("Session andrew not found.")

if __name__ == "__main__":
    activate_rotation()
