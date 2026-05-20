from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

def apply_crm_schema():
    load_dotenv()
    
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "admin")
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "BAPE_BD")
    
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    print(f"Connecting to: {host}:{port}/{db}")

    engine = create_engine(db_url)
    
    commands = [
        # WhatsAppSession
        "ALTER TABLE whatsapp_sessions ADD COLUMN IF NOT EXISTS respond_to_groups BOOLEAN DEFAULT FALSE",
        "ALTER TABLE whatsapp_sessions ADD COLUMN IF NOT EXISTS bot_whitelist_enabled BOOLEAN DEFAULT TRUE",
        "ALTER TABLE whatsapp_sessions ADD COLUMN IF NOT EXISTS bot_whitelist_numbers JSONB DEFAULT '[]'::jsonb",
        
        # Contact
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS is_excluded BOOLEAN DEFAULT FALSE",
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]'::jsonb",
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS internal_notes TEXT",
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS address TEXT",
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS birthday TEXT",
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS company_name TEXT",
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS job_title TEXT",
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS document_id TEXT",
        
        # AppointmentConfig
        "ALTER TABLE appointmentconfig ADD COLUMN IF NOT EXISTS reminder_rules JSONB DEFAULT '[]'::jsonb",
        
        # Appointment
        "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS reminders_sent JSONB DEFAULT '[]'::jsonb",
        "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS contact_id INTEGER REFERENCES contacts(id)"
    ]

    with engine.connect() as conn:
        print("Starting idempotent schema update...")
        for cmd in commands:
            try:
                # Use standard sqlalchemy execution for DDL
                conn.execute(text(cmd))
                conn.commit()
                # print(f"Executed: {cmd[:50]}...")
            except Exception as e:
                # print(f"Error executing {cmd[:30]}: {e}")
                conn.rollback()

    print("Idempotent CRM Schema update complete.")

if __name__ == "__main__":
    apply_crm_schema()
