from sqlmodel import SQLModel
from app.database import engine
from app.models import Contact, CompanySettings, KnowledgeDocument
from sqlalchemy import text

def apply_changes():
    # Drop specific tables to force recreation with new schema
    # WARNING: This deletes data in these tables.
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS knowledge_documents CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS company_settings CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS contacts CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS messages CASCADE")) 
        conn.execute(text("DROP TABLE IF EXISTS whatsapp_sessions CASCADE")) # New table logic
        conn.commit()
        
    print("Dropped tables.")
    
    # Recreate all tables (SQLModel will only create missing ones)
    SQLModel.metadata.create_all(engine)
    print("Recreated tables with new schema.")

if __name__ == "__main__":
    apply_changes()
