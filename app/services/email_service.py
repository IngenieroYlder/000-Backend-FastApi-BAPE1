import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    async def send_email(self, to_email: str, subject: str, body: str, company_id: int = None):
        """
        Sends an email using either company-specific settings or global defaults.
        """
        host = settings.SMTP_HOST
        port = settings.SMTP_PORT
        user = settings.SMTP_USER
        password = settings.SMTP_PASSWORD
        from_email = settings.SMTP_FROM_EMAIL
        
        # Try to load from DB if company_id is provided
        if company_id:
            try:
                from app.database import engine
                from sqlmodel import Session, select
                from app.models import CompanySettings
                
                with Session(engine) as session:
                    stmt = select(CompanySettings).where(CompanySettings.company_id == company_id)
                    comp_settings = session.exec(stmt).first()
                    
                    if comp_settings:
                        if comp_settings.smtp_host: host = comp_settings.smtp_host
                        if comp_settings.smtp_port: port = comp_settings.smtp_port
                        if comp_settings.smtp_user: user = comp_settings.smtp_user
                        if comp_settings.smtp_password: password = comp_settings.smtp_password
                        if comp_settings.smtp_from_email: from_email = comp_settings.smtp_from_email
            except Exception as e:
                logger.error(f"Error loading company settings for email: {e}")

        if not user or not password:
            logger.warning("SMTP not configured (User/Pass missing). Email not sent.")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = from_email or user
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'html'))

            server = smtplib.SMTP(host, port)
            server.starttls()
            server.login(user, password)
            text = msg.as_string()
            server.sendmail(user, to_email, text)
            server.quit()
            
            logger.info(f"Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

email_service = EmailService()
