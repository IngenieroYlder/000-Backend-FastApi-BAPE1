from sqlmodel import Session, select, func
from app.database import engine
from app.models import DocumentChunk, KnowledgeDocument

def check_chunks():
    with Session(engine) as session:
        doc_count = session.exec(select(func.count(KnowledgeDocument.id))).one()
        chunk_count = session.exec(select(func.count(DocumentChunk.id))).one()
        
        print(f"Total Documents: {doc_count}")
        print(f"Total Chunks: {chunk_count}")
        
        if doc_count > 0 and chunk_count == 0:
            print("CRITICAL: Documents exist but NO CHUNKS found. RAG processing failed.")
        elif chunk_count > 0:
            # Show sample
            chunk = session.exec(select(DocumentChunk).limit(1)).first()
            print(f"Sample Chunk ID: {chunk.id}, Doc ID: {chunk.document_id}")
            print(f"Content Preview: {chunk.content[:50]}...")
            print(f"Has Embedding: {bool(chunk.embedding)}")

if __name__ == "__main__":
    check_chunks()
