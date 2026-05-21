from sqlmodel import Session, text
from app.database import engine


def add_columns():
    commands = [
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS short_description VARCHAR",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS long_description TEXT",
        "ALTER TABLE services ADD COLUMN IF NOT EXISTS short_description VARCHAR",
        "ALTER TABLE services ADD COLUMN IF NOT EXISTS long_description TEXT",
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
    add_columns()
