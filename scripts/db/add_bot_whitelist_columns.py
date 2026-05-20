from sqlmodel import Session, text
from app.database import engine


def add_columns():
    commands = [
        "ALTER TABLE whatsapp_sessions ADD COLUMN IF NOT EXISTS bot_whitelist_enabled BOOLEAN DEFAULT TRUE",
        "ALTER TABLE whatsapp_sessions ADD COLUMN IF NOT EXISTS bot_whitelist_numbers JSONB DEFAULT '[]'::jsonb",
    ]

    with Session(engine) as session:
        for command in commands:
            try:
                session.execute(text(command))
                session.commit()
                print(f"Executed: {command}")
            except Exception as e:
                session.rollback()
                print(f"Error or already exists: {e}")


if __name__ == "__main__":
    add_columns()
