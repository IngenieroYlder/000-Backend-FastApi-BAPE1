from app.database import SessionLocal
from app.models import User
from app.auth import verify_password, get_password_hash

def debug_auth():
    db = SessionLocal()
    email = "admin@bape.com"
    password = "admin"
    
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User {email} NOT FOUND in database.")
            return

        print(f"User found: {user.email}")
        print(f"Stored Hash: {user.password_hash}")
        
        # Test Verification
        is_valid = verify_password(password, user.password_hash)
        print(f"Verification Result for '{password}': {is_valid}")

        if not is_valid:
            print("--- Mismatch Details ---")
            new_hash = get_password_hash(password)
            print(f"New Hash of '{password}': {new_hash}")
            print("Verify new hash:", verify_password(password, new_hash))
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_auth()
