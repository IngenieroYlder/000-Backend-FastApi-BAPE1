from sqlmodel import Session, select, create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

def check_db():
    with Session(engine) as session:
        # 1. Check Columns
        try:
            result = session.exec(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'company_settings'"))
            columns = [r[0] for r in result]
            print(f"Columns in company_settings: {columns}")
            
            if 'groq_api_key' not in columns:
                print("!!! MISSING COLUMN: groq_api_key !!!")
            else:
                print("Column 'groq_api_key' exists.")

        except Exception as e:
            print(f"Error checking schema: {e}")

        # 2. Check Values
        try:
            result = session.exec(text("SELECT id, company_id, openai_api_key, groq_api_key FROM company_settings"))
            for row in result:
                print(f"Row: {row}")
        except Exception as e:
            print(f"Error checking values: {e}")

if __name__ == "__main__":
    check_db()
