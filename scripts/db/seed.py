import logging
from sqlmodel import Session, select
from app.database import engine
from app.models import Plan, Company, User, UserRole
from passlib.context import CryptContext

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def seed_data():
    with Session(engine) as session:
        # 1. Create Default Plan
        plan = session.exec(select(Plan).where(Plan.name == "Free")).first()
        if not plan:
            plan = Plan(
                name="Free",
                price=0.0,
                limits={"agents": 1, "whatsapp_sessions": 1}
            )
            session.add(plan)
            session.commit()
            session.refresh(plan)
            logger.info(f"Created Plan: {plan.name}")
        else:
            logger.info(f"Plan already exists: {plan.name}")

        # 2. Create Default Company (for Superadmin)
        company = session.exec(select(Company).where(Company.name == "BAPE Admin")).first()
        if not company:
            company = Company(
                name="BAPE Admin",
                plan_id=plan.id,
                is_active=True
            )
            session.add(company)
            session.commit()
            session.refresh(company)
            logger.info(f"Created Company: {company.name}")
        else:
            logger.info(f"Company already exists: {company.name}")

        # 3. Create Superadmin User
        user = session.exec(select(User).where(User.email == "admin@bape.com")).first()
        if not user:
            user = User(
                email="admin@bape.com",
                hashed_password=get_password_hash("admin123"),
                first_name="Super",
                last_name="Admin",
                role=UserRole.SUPERADMIN,
                company_id=company.id,
                is_active=True
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info(f"Created Superadmin: {user.email}")
        else:
            logger.info(f"Superadmin already exists: {user.email}")

if __name__ == "__main__":
    seed_data()
