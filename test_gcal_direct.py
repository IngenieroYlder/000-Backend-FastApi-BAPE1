
import os
import datetime
import pytz
import json
import psycopg2
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

def get_data():
    load_dotenv()
    db_url = f"host={os.getenv('POSTGRES_HOST')} port={os.getenv('POSTGRES_PORT')} dbname={os.getenv('POSTGRES_DB')} user={os.getenv('POSTGRES_USER')} password={os.getenv('POSTGRES_PASSWORD')}"
    conn = psycopg2.connect(db_url)
    config = None
    appts = []
    try:
        cur = conn.cursor()
        # 1. Config
        cur.execute("SELECT id, google_calendar_id, google_access_token, google_refresh_token, google_client_id, google_client_secret, timezone FROM appointmentconfig LIMIT 1")
        row = cur.fetchone()
        if row:
            config = {
                "id": row[0],
                "google_calendar_id": row[1],
                "google_access_token": row[2],
                "google_refresh_token": row[3],
                "google_client_id": row[4],
                "google_client_secret": row[5],
                "timezone": row[6]
            }
        
        # 2. Appts for Feb 23
        cur.execute("SELECT id, title, start_time, google_event_id FROM appointments WHERE start_time >= '2026-02-23' AND start_time < '2026-02-24'")
        appts = cur.fetchall()
    finally:
        conn.close()
    return config, appts

def test_sync():
    config, appts = get_data()
    if not config:
        print("No AppointmentConfig found")
        return

    print(f"--- DATABASE LOCAL (Feb 23) ---")
    print(f"Found {len(appts)} local appointments on the 23rd.")
    local_g_ids = set()
    for r in appts:
        print(f"  Local: ID={r[0]}, Title={r[1]}, Start={r[2]}, GID={r[3]}")
        if r[3]: local_g_ids.add(r[3])

    print(f"\n--- GOOGLE CALENDAR (Upcoming from now) ---")
    client_id = config['google_client_id'] or os.getenv("GOOGLE_CLIENT_ID")
    client_secret = config['google_client_secret'] or os.getenv("GOOGLE_CLIENT_SECRET")
    
    creds = Credentials(
        token=config['google_access_token'],
        refresh_token=config['google_refresh_token'],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        # Search range for GCal: Feb 22 to Feb 25
        g_start = "2026-02-22T00:00:00Z"
        g_end = "2026-02-25T23:59:59Z"
        
        print(f"Fetching from GCal: {g_start} to {g_end}...")
        results = service.events().list(
            calendarId=config['google_calendar_id'] or 'primary',
            timeMin=g_start,
            timeMax=g_end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = results.get('items', [])
        print(f"Found {len(events)} events in GCal.")
        for event in events:
            ge_id = event.get('id')
            summary = event.get('summary', 'No Title')
            start = event['start'].get('dateTime', event['start'].get('date'))
            status = "[EXTERNAL]" if ge_id not in local_g_ids else "[MATCHED LOCAL]"
            print(f"  GCal: {start} | {summary} | ID={ge_id} {status}")
            
    except Exception as e:
        print(f"Error testing sync: {e}")

if __name__ == "__main__":
    test_sync()
