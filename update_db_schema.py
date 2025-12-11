from sqlalchemy import text
from app.database import engine

def update_schema():
    print("Updating database schema...")
    with engine.connect() as connection:
        # Add first_name column
        try:
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR"))
            print("Added first_name column.")
        except Exception as e:
            print(f"Error adding first_name: {e}")

        # Add last_name column
        try:
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR"))
            print("Added last_name column.")
        except Exception as e:
            print(f"Error adding last_name: {e}")

        # Add phone column
        try:
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR"))
            print("Added phone column.")
        except Exception as e:
            print(f"Error adding phone: {e}")
        
        connection.commit()
    print("Schema update complete.")

if __name__ == "__main__":
    update_schema()
