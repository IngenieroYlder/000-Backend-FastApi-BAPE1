import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'contacts';")
columns = cur.fetchall()
for col in columns:
    print(col)
cur.close()
conn.close()
