from sqlmodel import Session, select
from app.database import engine
from app.models import CompanySettings

def check_keys():
    with Session(engine) as session:
        stmt = select(CompanySettings).where(CompanySettings.company_id == 1)
        settings = session.exec(stmt).first()
        if settings:
            for key in ['openai_api_key', 'groq_api_key', 'gemini_api_key']:
                val = getattr(settings, key)
                if val:
                    print(f"{key}: '{val}'")
                    print(f"  Length: {len(val)}")
                    print(f"  Starts with: '{val[:10]}...'")
                    print(f"  Ends with: '...{val[-10:]}'")
                    print(f"  Has whitespace: {val != val.strip()}")
                else:
                    print(f"{key}: EMPTY")
        else:
            print("No settings found for company 1")

if __name__ == "__main__":
    check_keys()
