from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import engine
from sqlmodel import Session, select
from app import models
from app.config import settings, BAILEYS_ENGINE_URL
from datetime import datetime, timedelta
import httpx
import logging
import pytz

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        self.scheduler.add_job(self.check_reminders, 'interval', minutes=5)
        self.scheduler.start()
        logger.info("Scheduler started (5m interval).")

    async def check_reminders(self):
        logger.info("Checking for appointment reminders (Dynamic)...")
        with Session(engine) as session:
            now = datetime.utcnow()
            window_limit = now + timedelta(days=3)
            
            # Fetch confirmed appts
            stmt = select(models.Appointment).where(
                models.Appointment.status == 'confirmed',
                models.Appointment.start_time >= now,
                models.Appointment.start_time <= window_limit
            )
            appts = session.exec(stmt).all()
            
            for appt in appts:
                # 1. Get Company Appointment Config
                stmt_conf = select(models.AppointmentConfig).where(models.AppointmentConfig.company_id == appt.company_id)
                config = session.exec(stmt_conf).first()
                if not config or not config.reminder_rules:
                    continue
                
                rules = config.reminder_rules
                sent_ids = list(appt.reminders_sent or [])
                need_update = False
                
                for rule in rules:
                    rule_id = rule.get('id')
                    hours = rule.get('hours_before', 1)
                    
                    if rule_id in sent_ids:
                        continue
                    
                    # Target trigger time
                    trigger_time = appt.start_time - timedelta(hours=hours)
                    
                    # Check if trigger_time is now or in the past (but not too old)
                    # Use a 10-minute window since we run every 5m
                    if (now - timedelta(minutes=10)) <= trigger_time <= now:
                        logger.info(f"Triggering reminder {rule_id} for appt {appt.id}")
                        custom_msg = rule.get('message')
                        await self.send_reminder(session, appt, custom_msg)
                        
                        sent_ids.append(rule_id)
                        need_update = True
                
                if need_update:
                    appt.reminders_sent = sent_ids
                    session.add(appt)
                    session.commit()

    async def send_reminder(self, db_session, appt: models.Appointment, custom_message: str = None):
        stmt = select(models.WhatsAppSession).where(
            models.WhatsAppSession.company_id == appt.company_id,
            models.WhatsAppSession.status == 'connected'
        )
        wa_session = db_session.exec(stmt).first()
        
        if not wa_session:
            logger.warning(f"No active WA session for company {appt.company_id}. Reminder skipped.")
            return

        phone = appt.client_phone
        if '@' not in phone:
            phone = f"{phone}@s.whatsapp.net"

        if custom_message:
            # Simple template replacement
            msg_body = custom_message.replace('{name}', appt.client_name or '')
            msg_body = msg_body.replace('{date}', appt.start_time.strftime('%Y-%m-%d'))
            msg_body = msg_body.replace('{time}', appt.start_time.strftime('%H:%M'))
            msg_body = msg_body.replace('{title}', appt.title or '')
        else:
            msg_body = (
                f"🔔 *Recordatorio de Cita*\n\n"
                f"Hola {appt.client_name}, le recordamos que tiene una cita agendada:\n"
                f"📅 Fecha: {appt.start_time.strftime('%Y-%m-%d')}\n"
                f"⏰ Hora: {appt.start_time.strftime('%H:%M')}\n"
                f"📝 Motivo: {appt.title}\n\n"
                f"¡Los esperamos!"
            )

        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "session_name": wa_session.session_name,
                    "jid": phone,
                    "message": {"text": msg_body}
                }
                await client.post(f"{BAILEYS_ENGINE_URL}/message/send", json=payload)
                logger.info(f"Reminder sent to {phone}")
            except Exception as e:
                logger.error(f"Failed to send reminder to {phone}: {e}")

scheduler_service = SchedulerService()
