from sqlmodel import Session
from app.database import engine
from app.models import Contact, Message, MessageRole, MessageType

def inject_data():
    with Session(engine) as session:
        # Create Contact
        contact = Contact(company_id=1, phone="573001234567", name="Test User")
        session.add(contact)
        session.commit()
        session.refresh(contact)
        
        # Create Message
        msg = Message(
            company_id=1,
            contact_id=contact.id,
            role=MessageRole.USER,
            content="Hola, esto es una prueba.",
            type=MessageType.TEXT
        )
        session.add(msg)
        session.commit()
        print(f"Injected Contact {contact.id} and Message {msg.id}")

if __name__ == "__main__":
    inject_data()
