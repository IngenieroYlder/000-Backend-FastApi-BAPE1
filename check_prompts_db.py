from sqlmodel import Session, select
from app.database import engine
from app.models import WhatsAppSession, CompanySettings

def check_prompts():
    with Session(engine) as session:
        # Check instance prompt
        stmt = select(WhatsAppSession).where(WhatsAppSession.session_name == "company_1_andrew")
        wa_session = session.exec(stmt).first()
        if wa_session:
            print(f"--- Session Prompt (andrew) ---")
            print(f"'{wa_session.system_prompt}'")
        
        # Check global prompt
        stmt_settings = select(CompanySettings).where(CompanySettings.company_id == 1)
        settings = session.exec(stmt_settings).first()
        if settings:
            print(f"\n--- Global Company Prompt ---")
            print(f"'{settings.system_prompt}'")

if __name__ == "__main__":
    check_prompts()
