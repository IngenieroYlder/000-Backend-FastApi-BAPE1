from sqlmodel import Session, text
from app.database import engine


def add_column():
    commands = [
        "ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS image VARCHAR",
        "ALTER TABLE service_categories ADD COLUMN IF NOT EXISTS image VARCHAR",
    ]
    with Session(engine) as session:
        for command in commands:
            try:
                session.execute(text(command))
                session.commit()
                print(f"Executed: {command}")
            except Exception as e:
                session.rollback()
                print(f"Error or already applied: {e}")


if __name__ == "__main__":
    add_column()
