
import datetime
import pytz
from app.database import engine
from app.models import AppointmentConfig, Appointment
from sqlmodel import Session, select
from app.services.calendar_service import calendar_service

def debug_sync():
    with Session(engine) as session:
        # Get the first config
        config = session.exec(select(AppointmentConfig)).first()
        if not config:
            print("No AppointmentConfig found.")
            return

        print(f"Config found: ID={config.id}, TZ={config.timezone}, GCalID={config.google_calendar_id}")
        
        # Test range: Feb 23, 2026
        target_date = "2026-02-23"
        start_dt = datetime.datetime.strptime(target_date, "%Y-%m-%d")
        end_dt = start_dt + datetime.timedelta(days=1)
        
        # Local view
        stmt = select(Appointment).where(
            Appointment.company_id == config.company_id,
            Appointment.start_time >= start_dt,
            Appointment.start_time < end_dt
        )
        local_appts = session.exec(stmt).all()
        print(f"Local Appointments found: {len(local_appts)}")
        for a in local_appts:
            print(f"  - {a.title} ({a.start_time}) - GID: {a.google_event_id}")

        # Google Sync
        if config.google_refresh_token:
            print("Fetching from Google...")
            # Use UTC range for the API
            g_start = start_dt.replace(tzinfo=pytz.UTC)
            g_end = end_dt.replace(tzinfo=pytz.UTC)
            
            g_events = calendar_service.list_events(config, g_start, g_end)
            print(f"Google Events found: {len(g_events)}")
            for ge in g_events:
                ge_id = ge.get('id')
                summary = ge.get('summary', 'No Title')
                start = ge['start'].get('dateTime') or ge['start'].get('date')
                print(f"  - {summary} ({start}) - ID: {ge_id}")
                
                # Check duplication logic
                local_g_ids = {a.google_event_id for a in local_appts if a.google_event_id}
                if ge_id in local_g_ids:
                    print(f"    [MATCHED] Already in local DB.")
                else:
                    print(f"    [EXTERNAL] Not in local DB.")
        else:
            print("No Google Refresh Token in config.")

if __name__ == "__main__":
    debug_sync()
