from sqlmodel import Session, select
from app.database import engine
from app.models import Contact

def check_contacts():
    with Session(engine) as session:
        stmt = select(Contact).where(Contact.company_id == 1)
        contacts = session.exec(stmt).all()
        print(f"Total contacts: {len(contacts)}")
        for c in contacts:
            print(f"ID: {c.id} | Phone: {c.phone} | Name: {c.name}")

if __name__ == "__main__":
    check_contacts()
