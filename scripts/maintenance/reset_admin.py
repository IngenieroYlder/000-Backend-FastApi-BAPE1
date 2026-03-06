from sqlmodel import Session, select
from app.database import engine
from app.models import User, UserRole
from app.auth import get_password_hash

def reset_admin():
    print("Connecting to DB...")
    with Session(engine) as session:
        email = "admin@bape.com"
        password = "admin123"
        hashed = get_password_hash(password)
        
        stmt = select(User).where(User.email == email)
        user = session.exec(stmt).first()
        
        if user:
            print(f"User {email} found. Updating password...")
            user.password_hash = hashed
            session.add(user)
        else:
            print(f"User {email} not found. Creating new superadmin...")
            user = User(
                email=email, 
                password_hash=hashed,
                first_name="Super Admin",
                role=UserRole.SUPERADMIN,
                is_active=True,
                company_id=1
            )
            session.add(user)
        
        try:
            session.commit()
            print("\n" + "="*50)
            print("✅ ADMIN RESET SUCCESSFUL")
            print(f"Email: {email}")
            print(f"Password: {password}")
            print("="*50 + "\n")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    reset_admin()
