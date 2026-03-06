from fastapi import APIRouter, Request, BackgroundTasks, Depends, HTTPException
from app.database import get_session
from sqlmodel import Session, select
from app.models import Message, MessageRole, MessageType, Company, Contact, WhatsAppSession, CompanySettings
import logging
from datetime import datetime
from app.services.qr_cache import qr_cache
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    try:
        payload = await request.json()
        event = payload.get("event")
        session_name = payload.get("session_name")
        
        with open(settings.WEBHOOK_DEBUG_LOG, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] Event: {event} | Session: {session_name}\n")
        
        logger.info(f"Received webhook event: {event} for session: {session_name}")
        print(f"\n[WEBHOOK DEBUG] Event: {event} | Session: {session_name}")
        
        # Immediate Cache Update (Bypasses DB lag for UI)
        if event == "qr":
            qr_cache.set_qr(session_name, payload.get("qr"))
        elif event == "ready":
            qr_cache.set_status(session_name, "connected")
            
        if event == "message":
            msg_data = payload.get("message")
            media_path = payload.get("media_path")
            background_tasks.add_task(process_incoming_message_task, session_name, msg_data, media_path) 
        
        elif event == "qr":
            qr_code = payload.get("qr")
            background_tasks.add_task(update_session_qr_task, session_name, qr_code)
        
        elif event == "ready":
            background_tasks.add_task(update_session_status_task, session_name, "connected")

        return {"status": "received"}
    except Exception as e:
        logger.error(f"Webhook Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def update_session_qr_task(session_name: str, qr: str):
    from app.database import engine
    try:
        with Session(engine) as db_session:
            stmt = select(WhatsAppSession).where(WhatsAppSession.session_name.ilike(session_name))
            wa_session = db_session.exec(stmt).first()
            if wa_session:
                wa_session.qr_code = qr
                wa_session.status = "qr_ready"
                db_session.add(wa_session)
                db_session.commit()
    except Exception as e:
        logger.error(f"DB Error in update_session_qr_task: {e}")

def update_session_status_task(session_name: str, status: str):
    from app.database import engine
    try:
        with Session(engine) as db_session:
            stmt = select(WhatsAppSession).where(WhatsAppSession.session_name.ilike(session_name))
            wa_session = db_session.exec(stmt).first()
            if wa_session:
                wa_session.status = status.lower()
                wa_session.qr_code = None 
                db_session.add(wa_session)
                db_session.commit()
    except Exception as e:
        logger.error(f"DB Error in update_session_status_task: {e}")

async def process_incoming_message_task(session_name: str, msg_data: dict, media_path: str = None):
    from app.database import engine
    try:
        with Session(engine) as db_session:
            await process_incoming_message(session_name, msg_data, db_session, media_path)
    except Exception as e:
        logger.error(f"DB Error in process_incoming_message_task: {e}")

async def process_incoming_message(session_name: str, msg_data: dict, session: Session, media_path: str = None):
    try:
        print(f"\n[Incoming] Event for {session_name} | Raw JID: {msg_data.get('key', {}).get('remoteJid')}")
        # 1. Find the Session in DB
        stmt_sess = select(WhatsAppSession).where(WhatsAppSession.session_name.ilike(session_name))
        wa_session = session.exec(stmt_sess).first()
        
        if not wa_session:
            logger.error(f"Received message for unknown session: {session_name}")
            return

        print(f"[Webhook] Processing message for company {wa_session.company_id} | Phone: {wa_session.phone_number} | Alias: {wa_session.alias}")
        company_id = wa_session.company_id
        
        # Load Company Settings early
        stmt_settings = select(CompanySettings).where(CompanySettings.company_id == company_id)
        c_settings = session.exec(stmt_settings).first()
        image_prompt_fallback = c_settings.image_prompt if c_settings and c_settings.image_prompt else "El usuario ha enviado esta imagen. Analízala brevemente e intégrala a la conversación si es relevante."
        
        # Extract Contact Info
        key = msg_data.get("key", {})
        remote_jid = key.get("remoteJid") 
        
        is_group = "@g.us" in remote_jid
        is_channel = "@newsletter" in remote_jid
        
        if is_channel:
            return
            
        if is_group and not wa_session.respond_to_groups:
            return
            
        phone = remote_jid.split("@")[0]
        push_name = msg_data.get("pushName", phone)
        
        message_content = msg_data.get("message", {})
        text_content = ""
        msg_type = MessageType.TEXT
        media_url = None
        
        if "conversation" in message_content:
            text_content = message_content["conversation"]
        elif "extendedTextMessage" in message_content:
            text_content = message_content["extendedTextMessage"].get("text", "")
        elif "imageMessage" in message_content:
            msg_type = MessageType.IMAGE
            text_content = message_content["imageMessage"].get("caption", "")
            if media_path:
                import os
                media_url = f"/media/{os.path.basename(media_path)}"
        elif "audioMessage" in message_content:
            msg_type = MessageType.AUDIO
            if media_path:
                import os
                media_url = f"/media/{os.path.basename(media_path)}"
        elif "videoMessage" in message_content:
            msg_type = MessageType.VIDEO
            if media_path:
                import os
                media_url = f"/media/{os.path.basename(media_path)}"
        elif "documentMessage" in message_content:
            msg_type = MessageType.DOCUMENT
            if media_path:
                import os
                media_url = f"/media/{os.path.basename(media_path)}"

        ai_service = AIService()
        
        # Select best provider based on active config (mock logic for now)
        preferred_provider = wa_session.ai_provider or "openai" # Use session's preferred provider
        available_providers = []
        # Use c_settings (company settings) for API keys
        if c_settings:
            if c_settings.openai_api_key: available_providers.append(("openai", c_settings.openai_api_key))
            if c_settings.groq_api_key: available_providers.append(("groq", c_settings.groq_api_key))
            if c_settings.gemini_api_key: available_providers.append(("gemini", c_settings.gemini_api_key))
        
        if preferred_provider:
            available_providers.sort(key=lambda x: 0 if x[0] == preferred_provider else 1)

        if msg_type == MessageType.AUDIO and media_path:
            import os
            if os.path.exists(media_path):
                audio_providers = [p for p in available_providers if "audio" in ai_service.PROVIDER_CAPABILITIES.get(p[0], [])]
                transcription = None
                while audio_providers:
                    p_name, p_key = audio_providers[0]
                    try:
                        res = await ai_service.transcribe_audio(media_path, p_name, p_key)
                        if "Error:" not in res:
                            transcription = res
                            break
                        audio_providers.pop(0)
                    except Exception:
                        audio_providers.pop(0)
                if transcription:
                    text_content = f"{transcription} [Audio Transcrito]"

        if msg_type == MessageType.IMAGE and media_path:
            import os
            if os.path.exists(media_path):
                vision_providers = [p for p in available_providers if "vision" in ai_service.PROVIDER_CAPABILITIES.get(p[0], [])]
                analysis = None
                caption = message_content.get("imageMessage", {}).get("caption", "")
                prompt = caption if caption else image_prompt_fallback
                while vision_providers:
                    p_name, p_key = vision_providers[0]
                    try:
                        res = await ai_service.analyze_image(media_path, prompt, p_name, p_key)
                        if "Error:" not in res:
                            analysis = res
                            break
                        vision_providers.pop(0)
                    except Exception:
                        vision_providers.pop(0)
                if analysis:
                    text_content = f"[{text_content}] Descripción visual del bot: {analysis}" if text_content else f"Descripción visual del bot: {analysis}"

        if not text_content and msg_type == MessageType.TEXT:
             return 

        sender_lid = key.get("senderLid", "").split("@")[0] if key.get("senderLid") else None
        phone = remote_jid.split("@")[0]
        
        from app.models import Platform
        contact = None
        if sender_lid:
            stmt = select(Contact).where(Contact.company_id == company_id, Contact.phone == sender_lid)
            contact = session.exec(stmt).first()
        if not contact:
            stmt = select(Contact).where(Contact.company_id == company_id, Contact.phone == phone)
            contact = session.exec(stmt).first()
        
        if not contact:
            contact = Contact(
                company_id=company_id, 
                phone=sender_lid if sender_lid else phone, 
                name=push_name,
                platform=Platform.WHATSAPP
            )
            session.add(contact)
            session.commit()
            session.refresh(contact)
        else:
            contact.last_chat_date = datetime.utcnow()
            if contact.name == contact.phone and push_name != phone:
                contact.name = push_name
            session.add(contact)
            session.commit()
        
        new_msg = Message(
            company_id=company_id,
            contact_id=contact.id,
            session_id=wa_session.id,
            role=MessageRole.USER,
            content=text_content,
            type=msg_type,
            sender_name=push_name,
            media_url=media_url
        )
        session.add(new_msg)
        session.commit()
        
        valid_types = [MessageType.TEXT, MessageType.AUDIO, MessageType.IMAGE]
        if msg_type in valid_types and wa_session.is_bot_enabled and not contact.is_paused and not contact.is_excluded and text_content:
            from app.services.buffer_service import buffer_service
            buffer_data = {
                "company_id": company_id,
                "contact_id": contact.id,
                "wa_session_id": wa_session.id,
                "session_name": session_name,
                "remote_jid": remote_jid
            }
            await buffer_service.add_message(session_name, remote_jid, text_content, buffer_data, message_key=msg_data.get("key"))

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        print(f"[ERROR] Logic failed: {e}")
