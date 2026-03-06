from sqlmodel import Session, text
from app.database import engine

def update_schema():
    with Session(engine) as session:
        print("Adding SMTP columns to company_settings...")
        try:
            session.exec(text("ALTER TABLE company_settings ADD COLUMN smtp_host VARCHAR"))
            print("Added smtp_host")
        except Exception as e: print(f"smtp_host might exist: {e}")

        try:
            session.exec(text("ALTER TABLE company_settings ADD COLUMN smtp_port INTEGER"))
            print("Added smtp_port")
        except Exception as e: print(f"smtp_port might exist: {e}")

        try:
            session.exec(text("ALTER TABLE company_settings ADD COLUMN smtp_user VARCHAR"))
            print("Added smtp_user")
        except Exception as e: print(f"smtp_user might exist: {e}")

        try:
            session.exec(text("ALTER TABLE company_settings ADD COLUMN smtp_password VARCHAR"))
            print("Added smtp_password")
        except Exception as e: print(f"smtp_password might exist: {e}")

        try:
            session.exec(text("ALTER TABLE company_settings ADD COLUMN smtp_from_email VARCHAR"))
            print("Added smtp_from_email")
        except Exception as e: print(f"smtp_from_email might exist: {e}")
        
        session.commit()
        print("Schema update complete.")

if __name__ == "__main__":
    update_schema()
