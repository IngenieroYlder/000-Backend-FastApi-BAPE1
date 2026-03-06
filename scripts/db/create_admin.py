from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash

def create_admin():
    db = SessionLocal()
    email = "admin@bape.com"
    password = "admin"
    
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"El usuario {email} ya existe.")
            return

        # Create user
        new_user = User(email=email, password_hash=get_password_hash(password))
        db.add(new_user)
        db.commit()
        print(f"El usuario {email} se ha creado exitosamente!")
        print(f"Email: {email}")
        print(f"Password: {password}")
    except Exception as e:
        print(f"Error al crear el usuario: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
