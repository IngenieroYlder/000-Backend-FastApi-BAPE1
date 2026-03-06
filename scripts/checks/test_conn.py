import psycopg2
from app.config import settings

print("Testing connection...")
print(f"User: {settings.POSTGRES_USER}")
print(f"DB: {settings.POSTGRES_DB}")
print(f"Host: {settings.POSTGRES_HOST}")
# password hidden

try:
    conn = psycopg2.connect(
        host=settings.POSTGRES_HOST,
        database=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        port=settings.POSTGRES_PORT,
        options="-c client_encoding=UTF8"
    )
    print("Connection Successful!")
    conn.close()
except Exception as e:
    print("Connection Failed!")
    if hasattr(e, 'pgcode'):
        print(f"PG Code: {e.pgcode}")
    print(f"Error Type: {type(e)}")
    # Do not print 'e' directly to avoid UnicodeDecodeError
