from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlmodel import Session, select
from app import models, auth
from app.database import get_session, engine
import httpx
import logging
import asyncio
from app.config import BAILEYS_ENGINE_URL
from app.services.qr_cache import qr_cache

router = APIRouter(
    prefix="/whatsapp",
    tags=["WhatsApp Multi-Instance"]
)

logger = logging.getLogger(__name__)

@router.get("/sessions", response_model=List[models.WhatsAppSession])
async def get_sessions(db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    """List all WhatsApp instances for the company with Cache Fallback"""
    try:
        # Try to get sessions from DB with a timeout
        # Since SQLAlchemy doesn't have a simple async timeout for exec(), we use a wrapper or cache first
        
        # Strategy: Return cache immediately if DB is known to be slow? 
        # Or try for 2 seconds.
        try:
            sessions = await asyncio.wait_for(asyncio.to_thread(_get_sessions_sync, db, current_user.company_id), timeout=2.0)
            
            # Update Cache with fresh data from DB
            for s in sessions:
                qr_cache.update_metadata(s.session_name, {
                    "id": s.id,
                    "alias": s.alias,
                    "ai_provider": s.ai_provider,
                    "ai_strategy": s.ai_strategy,
                    "is_bot_enabled": s.is_bot_enabled,
                    "respond_to_groups": s.respond_to_groups,
                    "company_id": s.company_id,
                    "status": s.status
                })
            
            # Merge with live QR/Status from engines
            for s in sessions:
                cache_data = qr_cache.get(s.session_name)
                if cache_data:
                    s.status = cache_data["status"]
                    if cache_data["qr"]:
                        s.qr_code = cache_data["qr"]
            
            return sessions
        except asyncio.TimeoutError:
            logger.warning(f"Database timeout for company {current_user.company_id}, returning cache.")
            cached_sessions = qr_cache.get_all_for_company(current_user.company_id)
            if not cached_sessions:
                # Emergency: If cache is empty, return a placeholder for known sessions if any
                # (This part is tricky without DB access at all)
                return []
            return [models.WhatsAppSession(**s) for s in cached_sessions]

    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return [models.WhatsAppSession(**s) for s in qr_cache.get_all_for_company(current_user.company_id)]

def _get_sessions_sync(db: Session, company_id: int):
    stmt = select(models.WhatsAppSession).where(models.WhatsAppSession.company_id == company_id)
    return db.exec(stmt).all()

@router.post("/sessions", response_model=models.WhatsAppSession)
async def create_session(
    alias: str, 
    ai_provider: str = "openai",
    ai_strategy: str = "fixed",
    db: Session = Depends(get_session), 
    current_user: models.User = Depends(auth.get_current_user)
):
    """Create a new WhatsApp instance config"""
    safe_alias = "".join(c for c in alias if c.isalnum())
    session_name = f"company_{current_user.company_id}_{safe_alias}"
    
    def _create_sync():
        stmt = select(models.WhatsAppSession).where(models.WhatsAppSession.session_name == session_name)
        if db.exec(stmt).first():
            return None
        new_session = models.WhatsAppSession(
            session_name=session_name,
            alias=alias,
            company_id=current_user.company_id,
            status="disconnected",
            ai_provider=ai_provider,
            ai_strategy=ai_strategy
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session

    try:
        new_session = await asyncio.wait_for(asyncio.to_thread(_create_sync), timeout=2.0)
        if not new_session:
            raise HTTPException(status_code=400, detail="Ya existe una sesión con ese alias")
    except asyncio.TimeoutError:
        logger.warning("DB Timeout in create_session. Forcing cache creation.")
        # Create a fake session object to return so UI proceeds
        import time
        fake_id = int(time.time() % 10000)
        new_session = models.WhatsAppSession(
            id=fake_id,
            session_name=session_name,
            alias=alias,
            company_id=current_user.company_id,
            status="disconnected",
            ai_provider=ai_provider,
            ai_strategy=ai_strategy
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    # Pre-populate cache immediately
    qr_cache.update_metadata(session_name, {
        "id": new_session.id,
        "alias": alias,
        "ai_provider": ai_provider,
        "ai_strategy": ai_strategy,
        "is_bot_enabled": True,
        "respond_to_groups": False,
        "company_id": current_user.company_id,
        "status": "disconnected"
    })
    
    return new_session

@router.post("/sessions/{session_id}/init")
async def init_session(
    session_id: int, 
    request: Request,
    db: Session = Depends(get_session), 
    current_user: models.User = Depends(auth.get_current_user)
):
    """Start the Baileys session to generate QR"""
    session_name = None
    
    def _update_sync():
        session = db.get(models.WhatsAppSession, session_id)
        if session and session.company_id == current_user.company_id:
            session.status = "initializing"
            db.add(session)
            db.commit()
            return session.session_name
        return None

    try:
        session_name = await asyncio.wait_for(asyncio.to_thread(_update_sync), timeout=2.0)
    except asyncio.TimeoutError:
        name, data = qr_cache.get_by_id(session_id)
        if name and data["metadata"].get("company_id") == current_user.company_id:
            session_name = name
    except Exception:
        pass

    if not session_name:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    qr_cache.set_status(session_name, "initializing")

    # Call Baileys Engine
    import os
    base_url = os.getenv("BASE_PUBLIC_URL", "http://127.0.0.1:8003")
    webhook_url = f"{base_url.rstrip('/')}/webhook"
    
    payload = {
        "session_name": session_name,
        "webhook_url": webhook_url
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{BAILEYS_ENGINE_URL}/session/init", json=payload)
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail="Error al iniciar motor Baileys")
        except Exception:
            raise HTTPException(status_code=500, detail="Motor Baileys no disponible")
            
    return {"status": "initializing", "message": "Iniciando sesión..."}

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    """Remove a session"""
    session_name = None
    def _delete_sync():
        session = db.get(models.WhatsAppSession, session_id)
        if session and session.company_id == current_user.company_id:
            name = session.session_name
            db.delete(session)
            db.commit()
            return name
        return None

    try:
        session_name = await asyncio.wait_for(asyncio.to_thread(_delete_sync), timeout=2.0)
    except asyncio.TimeoutError:
        name, data = qr_cache.get_by_id(session_id)
        if name and data["metadata"].get("company_id") == current_user.company_id:
            session_name = name
    except Exception:
        pass

    if not session_name:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
    # Remove from cache
    if session_name in qr_cache.cache:
        del qr_cache.cache[session_name]

    # Delete from Baileys?
    async with httpx.AsyncClient() as client:
        try:
             await client.delete(f"{BAILEYS_ENGINE_URL}/session/{session_name}")
        except Exception:
             pass

    return {"status": "deleted"}

@router.post("/sessions/{session_id}/reset")
async def reset_session(
    session_id: int, 
    request: Request,
    db: Session = Depends(get_session), 
    current_user: models.User = Depends(auth.get_current_user)
):
    """Delete session files and re-initialize (Fixes Bad MAC)"""
    session_name = None
    def _update_sync():
        session = db.get(models.WhatsAppSession, session_id)
        if session and session.company_id == current_user.company_id:
            session.status = "initializing"
            db.add(session)
            db.commit()
            return session.session_name
        return None

    try:
        session_name = await asyncio.wait_for(asyncio.to_thread(_update_sync), timeout=2.0)
    except asyncio.TimeoutError:
        name, data = qr_cache.get_by_id(session_id)
        if name and data["metadata"].get("company_id") == current_user.company_id:
            session_name = name
    except Exception:
        pass

    if not session_name:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    qr_cache.set_status(session_name, "initializing")

    base_url = str(request.base_url).rstrip('/')
    webhook_url = f"{base_url}/webhook"

    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "session_name": session_name,
                "webhook_url": webhook_url
            }
            resp = await client.post(f"{BAILEYS_ENGINE_URL}/session/reset", json=payload)
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail="Error resetting session")
        except Exception:
            raise HTTPException(status_code=500, detail="Motor Baileys no disponible")

    return {"status": "resetting", "message": "Reiniciando sesión..."}

@router.post("/sessions/{session_id}/repair")
async def repair_session(
    session_id: int, 
    request: Request,
    db: Session = Depends(get_session), 
    current_user: models.User = Depends(auth.get_current_user)
):
    """Delete corrupted pre-keys but keep creds (Fixes Bad MAC without re-pairing)"""
    session_name = None
    def _update_sync():
        session = db.get(models.WhatsAppSession, session_id)
        if session and session.company_id == current_user.company_id:
            session.status = "initializing"
            db.add(session)
            db.commit()
            return session.session_name
        return None

    try:
        session_name = await asyncio.wait_for(asyncio.to_thread(_update_sync), timeout=2.0)
    except asyncio.TimeoutError:
        name, data = qr_cache.get_by_id(session_id)
        if name and data["metadata"].get("company_id") == current_user.company_id:
            session_name = name
    except Exception:
        pass

    if not session_name:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    qr_cache.set_status(session_name, "initializing")

    base_url = str(request.base_url).rstrip('/')
    webhook_url = f"{base_url}/webhook"

    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "session_name": session_name,
                "webhook_url": webhook_url
            }
            resp = await client.post(f"{BAILEYS_ENGINE_URL}/session/repair", json=payload)
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail="Error repairing session")
        except Exception:
            raise HTTPException(status_code=500, detail="Motor Baileys no disponible")

    return {"status": "repairing", "message": "Reparando sesión..."}

@router.post("/sessions/{session_id}/status")
async def publish_status(
    session_id: int, 
    text: str,
    db: Session = Depends(get_session), 
    current_user: models.User = Depends(auth.get_current_user)
):
    """Publish a text status to WhatsApp"""
    session_name = None
    def _get_sync():
        session = db.get(models.WhatsAppSession, session_id)
        if session and session.company_id == current_user.company_id:
            if session.status != "connected":
                 raise HTTPException(status_code=400, detail="La sesión no está conectada")
            return session.session_name
        return None

    try:
        session_name = await asyncio.wait_for(asyncio.to_thread(_get_sync), timeout=2.0)
    except asyncio.TimeoutError:
        name, data = qr_cache.get_by_id(session_id)
        if name and data["metadata"].get("company_id") == current_user.company_id:
             if data["status"] != "connected":
                  raise HTTPException(status_code=400, detail="La sesión no está conectada")
             session_name = name
    except HTTPException as he:
        raise he
    except Exception:
        pass

    if not session_name:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    payload = {
        "session_name": session_name,
        "jid": "status@broadcast",
        "message": {"text": text}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{BAILEYS_ENGINE_URL}/message/send", json=payload)
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Error en motor: {resp.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")
            
    return {"status": "success", "message": "Estado publicado"}

@router.put("/sessions/{session_id}/config")
async def update_session_config(
    session_id: int,
    respond_to_groups: Optional[bool] = None,
    is_bot_enabled: Optional[bool] = None,
    ai_provider: Optional[str] = None,
    ai_strategy: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Update session bot configuration"""
    session_dict = None
    
    def _update_sync():
        session = db.get(models.WhatsAppSession, session_id)
        if not session or session.company_id != current_user.company_id:
            return None
        
        if respond_to_groups is not None:
            session.respond_to_groups = respond_to_groups
        if is_bot_enabled is not None:
            session.is_bot_enabled = is_bot_enabled
        if ai_provider is not None:
            session.ai_provider = ai_provider
        if ai_strategy is not None:
            session.ai_strategy = ai_strategy
            
        db.add(session)
        db.commit()
        db.refresh(session)
        return session.dict()

    try:
        session_dict = await asyncio.wait_for(asyncio.to_thread(_update_sync), timeout=2.0)
    except asyncio.TimeoutError:
        name, data = qr_cache.get_by_id(session_id)
        if name and data["metadata"].get("company_id") == current_user.company_id:
             updates = {}
             if respond_to_groups is not None: updates["respond_to_groups"] = respond_to_groups
             if is_bot_enabled is not None: updates["is_bot_enabled"] = is_bot_enabled
             if ai_provider is not None: updates["ai_provider"] = ai_provider
             if ai_strategy is not None: updates["ai_strategy"] = ai_strategy
             
             qr_cache.update_metadata(name, updates)
             name, fresh_data = qr_cache.get_by_id(session_id)
             session_dict = fresh_data["metadata"]
    except Exception:
        pass
        
    if not session_dict:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
    return session_dict
