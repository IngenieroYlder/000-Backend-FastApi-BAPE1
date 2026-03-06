from sqlmodel import Session, select
from app.database import engine
from app.models import WhatsAppSession

def check_strategy():
    with Session(engine) as session:
        stmt = select(WhatsAppSession).where(WhatsAppSession.session_name == "company_1_andrew")
        wa_session = session.exec(stmt).first()
        if wa_session:
            print(f"Session: {wa_session.session_name}")
            print(f"Provider: {wa_session.ai_provider}")
            print(f"Strategy: {wa_session.ai_strategy}")
        else:
            print("Session andrew not found.")

if __name__ == "__main__":
    check_strategy()
