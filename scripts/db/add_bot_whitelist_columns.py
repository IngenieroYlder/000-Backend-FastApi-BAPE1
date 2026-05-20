from sqlmodel import Session, text
from app.database import engine


def add_columns():
    commands = [
        "ALTER TABLE whatsapp_sessions ADD COLUMN IF NOT EXISTS bot_whitelist_enabled BOOLEAN DEFAULT FALSE",
        "ALTER TABLE whatsapp_sessions ADD COLUMN IF NOT EXISTS bot_whitelist_numbers JSONB DEFAULT '[]'::jsonb",
        # Apaga la whitelist para canales existentes que ya tienen TRUE por la migracion vieja
        "UPDATE whatsapp_sessions SET bot_whitelist_enabled = FALSE WHERE bot_whitelist_numbers IS NULL OR jsonb_array_length(COALESCE(bot_whitelist_numbers, '[]'::jsonb)) = 0",
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
