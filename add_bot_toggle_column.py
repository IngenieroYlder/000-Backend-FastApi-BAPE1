from sqlmodel import Session, create_engine, text
from app.database import engine

def add_column():
    with Session(engine) as session:
        try:
            session.execute(text("ALTER TABLE whatsapp_sessions ADD COLUMN is_bot_enabled BOOLEAN DEFAULT TRUE"))
            session.commit()
            print("Column is_bot_enabled added successfully.")
        except Exception as e:
            print(f"Error or already exists: {e}")

if __name__ == "__main__":
    add_column()
