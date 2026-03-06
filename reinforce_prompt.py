from sqlmodel import Session, select
from app.database import engine
from app.models import WhatsAppSession, CompanySettings

def reinforce_prompt():
    golden_rules = "\n\n### REGLAS DE ORO:\n- NUNCA menciones detalles técnicos, límites de tokens o errores de API al cliente.\n- Si hay un error, discúlpate de forma natural y sugiere intentar más tarde.\n- Mantén un tono profesional y amable."
    
    with Session(engine) as session:
        # Update session prompt
        stmt = select(WhatsAppSession).where(WhatsAppSession.session_name == "company_1_andrew")
        wa_session = session.exec(stmt).first()
        if wa_session:
            current_prompt = wa_session.system_prompt or ""
            if "REGLAS DE ORO" not in current_prompt:
                wa_session.system_prompt = current_prompt + golden_rules
                session.add(wa_session)
                print("Reinforced andrew session prompt.")
        
        # Update global prompt
        stmt_settings = select(CompanySettings).where(CompanySettings.company_id == 1)
        settings = session.exec(stmt_settings).first()
        if settings:
            current_settings_prompt = settings.system_prompt or ""
            if "REGLAS DE ORO" not in current_settings_prompt:
                settings.system_prompt = current_settings_prompt + golden_rules
                session.add(settings)
                print("Reinforced global company prompt.")
        
        session.commit()

if __name__ == "__main__":
    reinforce_prompt()
