from sqlmodel import Session, text
from app.database import engine


def add_column():
    commands = [
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS is_group BOOLEAN DEFAULT FALSE",
        # Backfill: any phone that is too long to be a real number or starts
        # with WhatsApp's modern group/community prefix is treated as a group.
        "UPDATE contacts SET is_group = TRUE "
        "WHERE is_group = FALSE AND (LENGTH(phone) >= 15 OR phone LIKE '120363%')",
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
