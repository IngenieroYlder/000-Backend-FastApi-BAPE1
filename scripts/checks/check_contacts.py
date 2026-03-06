from sqlmodel import Session, select, create_engine
from app.models import Contact, Company
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

def check_contacts():
    with Session(engine) as session:
        contacts = session.exec(select(Contact)).all()
        print(f"--- CONTACTS ({len(contacts)}) ---")
        for c in contacts:
            print(f"ID: {c.id} | Phone: {c.phone} | Name: {c.name} | CompanyID: {c.company_id}")

        companies = session.exec(select(Company)).all()
        print(f"--- COMPANIES ({len(companies)}) ---")
        for comp in companies:
            print(f"ID: {comp.id} | Name: {comp.name}")

if __name__ == "__main__":
    check_contacts()
