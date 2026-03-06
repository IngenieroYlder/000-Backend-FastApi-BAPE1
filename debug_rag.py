import asyncio
from app.services.rag_service import rag_service
from app.database import engine
from sqlmodel import Session, select
from app.models import KnowledgeDocument

async def debug_rag():
    with Session(engine) as session:
        # Get the latest document
        doc = session.exec(select(KnowledgeDocument).order_by(KnowledgeDocument.id.desc()).limit(1)).first()
        
        if not doc:
            print("No documents found.")
            return

        print(f"Processing Document ID: {doc.id}, Filename: {doc.filename}")
        print(f"Content Length: {len(doc.content) if doc.content else 0}")
        
        if not doc.content:
            print("WARNING: Document has no content!")
            return

        # Check API Key presence
        from app.models import CompanySettings
        settings = session.exec(select(CompanySettings).where(CompanySettings.company_id == doc.company_id)).first()
        if settings:
            print(f"Company Settings Found.")
            print(f"OpenAI Key Configured: {bool(settings.openai_api_key)}")
            print(f"Groq Key Configured: {bool(settings.groq_api_key)}")
            
            if settings.openai_api_key:
                print(f"OpenAI Key Preview: {settings.openai_api_key[:5]}...")
            if settings.groq_api_key:
                print(f"Groq Key Preview: {settings.groq_api_key[:5]}...")
        else:
            print("CRITICAL: No CompanySettings found for this company.")

        # Manually trigger processing
        try:
            await rag_service.process_document(doc.id)
            print("Processing completed successfully.")
        except Exception as e:
            print(f"ERROR during processing: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_rag())
