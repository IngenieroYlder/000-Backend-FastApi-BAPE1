from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select
from app.database import get_session
from app import models, auth
from typing import List, Optional
import httpx
import logging

router = APIRouter(
    prefix="/chats",
    tags=["Chats"]
)

logger = logging.getLogger(__name__)
from app.config import BAILEYS_ENGINE_URL

@router.get("/", response_model=List[models.Contact])
def get_chats(db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    # Get all contacts for the company, ordered by last activity (simplified)
    # In a real app, you'd join with messages and order by max(message.created_at)
    stmt = select(models.Contact).where(models.Contact.company_id == current_user.company_id)
    contacts = db.exec(stmt).all()
    return contacts

@router.get("/{contact_id}/messages", response_model=List[models.Message])
def get_messages(contact_id: int, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    # Check contact belongs to company
    contact = db.get(models.Contact, contact_id)
    if not contact or contact.company_id != current_user.company_id:
         raise HTTPException(status_code=404, detail="Contact not found")
         
    stmt = select(models.Message).where(models.Message.contact_id == contact_id).order_by(models.Message.created_at)
    messages = db.exec(stmt).all()
    return messages

@router.post("/{contact_id}/send")
async def send_message(
    contact_id: int, 
    payload: dict = Body(...), 
    db: Session = Depends(get_session), 
    current_user: models.User = Depends(auth.get_current_user)
):
    content = payload.get("content")
    if not content:
        raise HTTPException(status_code=422, detail="Message content required")

    # 1. Verify Contact
    contact = db.get(models.Contact, contact_id)
    if not contact or contact.company_id != current_user.company_id:
         raise HTTPException(status_code=404, detail="Contact not found")

    # 2. Save Message to DB (Optimistic)
    new_msg = models.Message(
        company_id=current_user.company_id,
        contact_id=contact.id,
        role=models.MessageRole.ASSISTANT,
        content=content,
        type=models.MessageType.TEXT
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)

    # 3. Send via Baileys
    # Find active session for this company
    stmt_session = select(models.WhatsAppSession).where(
        models.WhatsAppSession.company_id == current_user.company_id,
        models.WhatsAppSession.status == "connected"
    )
    wa_session = db.exec(stmt_session).first()
    
    if not wa_session:
        # Check if there's any session at all
        any_session = db.exec(select(models.WhatsAppSession).where(models.WhatsAppSession.company_id == current_user.company_id)).first()
        if any_session:
            detail = f"La sesión WhatsApp ({any_session.alias}) está en estado: {any_session.status}. Debe estar 'connected' para enviar mensajes."
        else:
            detail = "No hay ninguna sesión de WhatsApp vinculada para esta cuenta."
            
        raise HTTPException(status_code=400, detail=detail)

    session_name = wa_session.session_name
    # Group JIDs end with @g.us, individual chats with @s.whatsapp.net.
    # Fallback for legacy contacts saved before is_group existed: long numeric
    # phones (>=15 digits) or the modern community/group prefix.
    looks_like_group = (
        getattr(contact, "is_group", False)
        or len(contact.phone) >= 15
        or contact.phone.startswith("120363")
    )
    jid = f"{contact.phone}@g.us" if looks_like_group else f"{contact.phone}@s.whatsapp.net"
    logger.info(f"[chat.send] session={session_name} jid={jid} (group={looks_like_group})")

    try:
        async with httpx.AsyncClient() as client:
            baileys_payload = {
                "session_name": session_name,
                "jid": jid,
                "message": {"text": content}
            }
            resp = await client.post(f"{BAILEYS_ENGINE_URL}/message/send", json=baileys_payload)

            if resp.status_code != 200:
                logger.error(f"Baileys Send Error ({resp.status_code}): {resp.text}")
                raise HTTPException(status_code=500, detail=f"Baileys rejected the message: {resp.text}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return new_msg

@router.post("/{contact_id}/pause")
def pause_bot(
    contact_id: int, 
    payload: dict = Body(...),
    db: Session = Depends(get_session), 
    current_user: models.User = Depends(auth.get_current_user)
):
    paused = payload.get("paused", True)
    
    contact = db.get(models.Contact, contact_id)
    if not contact or contact.company_id != current_user.company_id:
         raise HTTPException(status_code=404, detail="Contact not found")
         
    contact.is_paused = paused
    if paused:
        contact.paused_until = None # Indefinite pause, or set time if provided
    else:
        contact.paused_until = None
        
    db.add(contact)
    db.commit()
    return {"status": "paused" if paused else "resumed", "is_paused": paused}
