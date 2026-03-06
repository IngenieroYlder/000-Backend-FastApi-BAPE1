import json
import numpy as np
from typing import List, Dict, Optional
from sqlmodel import Session, select
from sqlalchemy import delete
from app.database import engine
from app.models import KnowledgeDocument, DocumentChunk
from app.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.chunk_size = 1000
        self.overlap = 200

    def chunk_text(self, text: str) -> List[str]:
        """
        Splits text into chunks of roughly `chunk_size` characters with `overlap`.
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + self.chunk_size
            
            # If we are not at the end, try to find a space/newline to break cleanly
            if end < text_len:
                # Search for the last space/newline within the last 100 chars of the chunk
                last_space = -1
                for i in range(end, max(start, end - 100), -1):
                    if text[i] in [' ', '\n', '.', '!', '?']:
                        last_space = i
                        break
                
                if last_space != -1:
                    end = last_space + 1 # Include the delimiter
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start forward, accounting for overlap
            start += (self.chunk_size - self.overlap)
            
        return chunks

    async def process_document(self, document_id: int):
        """
        Chunks and embeds a document. Saves to DB.
        """
        with Session(engine) as session:
            doc = session.get(KnowledgeDocument, document_id)
            if not doc or not doc.content:
                print(f"[RAG] Document {document_id} has no content.")
                return

            # Clear existing chunks
            session.exec(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
            session.commit()
            
            # Chunking
            print(f"[RAG] Chunking document {doc.filename}...")
            text_chunks = self.chunk_text(doc.content)
            
            # Embedding & Saving
            print(f"[RAG] Generating embeddings for {len(text_chunks)} chunks...")
            
            # Fetch Company Settings for API Key
            from app.models import CompanySettings
            settings = session.exec(select(CompanySettings).where(CompanySettings.company_id == doc.company_id)).first()
            api_key = settings.openai_api_key if settings else None
            
            for i, text in enumerate(text_chunks):
                # Pass API Key explicitly
                embedding = await ai_service.get_embedding(text, api_key)
                if embedding:
                    chunk = DocumentChunk(
                        document_id=doc.id,
                        chunk_index=i,
                        content=text,
                        embedding=json.dumps(embedding) # Store as JSON string
                    )
                    session.add(chunk)
                else:
                    print(f"[RAG] Failed to get embedding for chunk {i}")
            
            session.commit()
            print(f"[RAG] Document {document_id} processed successfully.")

    async def retrieve_context(self, query: str, company_id: int, limit: int = 5) -> str:
        """
        Retrieves the most relevant document chunks for the query.
        """
        # 1. Embed Query
        query_embedding = await ai_service.get_embedding(query)
        if not query_embedding:
            return ""
        
        query_vec = np.array(query_embedding)
        
        # 2. Fetch all chunks for the company (Optimization: Cache this or use PGVector later)
        # For now, fetching all is okay for prototype (thousands of chunks is fine in memory)
        with Session(engine) as session:
            # Join DocumentChunk with KnowledgeDocument to filter by company
            statement = select(DocumentChunk).join(KnowledgeDocument).where(KnowledgeDocument.company_id == company_id)
            all_chunks = session.exec(statement).all()
            
            if not all_chunks:
                return ""
            
            # 3. Calculate Similarities
            scores = []
            for chunk in all_chunks:
                if not chunk.embedding:
                    continue
                
                try:
                    chunk_vec = np.array(json.loads(chunk.embedding))
                    
                    # Robust Cosine Similarity: (A . B) / (||A|| * ||B||)
                    norm_query = np.linalg.norm(query_vec)
                    norm_chunk = np.linalg.norm(chunk_vec)
                    
                    if norm_query == 0 or norm_chunk == 0:
                        similarity = 0
                    else:
                        similarity = np.dot(query_vec, chunk_vec) / (norm_query * norm_chunk)
                        
                    scores.append((similarity, chunk.content, chunk.document.filename))
                except Exception as e:
                    print(f"Error parsing embedding: {e}")
                    continue
            
            # 4. Sort and Select Top K
            scores.sort(key=lambda x: x[0], reverse=True)
            top_chunks = scores[:limit]
            
            # 5. Format Context
            context_text = "\n\n### FUENTE DE CONOCIMIENTO (Fragmentos Relevantes):\n"
            for score, content, filename in top_chunks:
                context_text += f"\n--- DEL DOCUMENTO: {filename} (Relevancia: {score:.2f}) ---\n{content}\n"
                
            return context_text

rag_service = RAGService()
