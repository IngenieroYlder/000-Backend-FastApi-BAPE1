from sqlmodel import Session, select, delete
from app.database import engine
from app.models import Message, Contact

def perform_fixes():
    with Session(engine) as session:
        # 1. DELETE Technical Errors from history
        # Case insensitive check for "Error:" or "Groq Error" or JSON error structures
        to_delete = session.exec(select(Message).where(
            (Message.content.like("%Error:%")) | 
            (Message.content.like("%Groq Error%")) |
            (Message.content.like("%rate_limit_exceeded%"))
        )).all()
        
        print(f"Deleting {len(to_delete)} error messages...")
        for m in to_delete:
            session.delete(m)
        session.commit()

        # 2. CONTACT MERGE: ID 1 (Phone) -> ID 2 (LID)
        c1 = session.get(Contact, 1) # Phone-based
        c2 = session.get(Contact, 2) # LID-based
        
        if c1 and c2:
            print(f"Merging contact {c1.id} ({c1.phone}) into {c2.id} ({c2.phone})")
            
            # Reassign messages
            stmt_msgs = select(Message).where(Message.contact_id == c1.id)
            msgs = session.exec(stmt_msgs).all()
            for m in msgs:
                m.contact_id = c2.id
                session.add(m)
            
            # Transfer notes/summary if c2 is empty and c1 has data
            if not c2.summary and c1.summary:
                c2.summary = c1.summary
            if not c2.internal_notes and c1.internal_notes:
                c2.internal_notes = c1.internal_notes
            
            session.add(c2)
            session.delete(c1)
            session.commit()
            print("Merge successful.")
        else:
            print(f"Merge skipped. Contacts found: c1={c1 is not None}, c2={c2 is not None}")

if __name__ == "__main__":
    perform_fixes()
