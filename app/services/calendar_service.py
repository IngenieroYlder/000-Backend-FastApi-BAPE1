import os
import datetime
from typing import List, Optional, Dict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from sqlmodel import Session, select
from app.database import engine
from app.models import AppointmentConfig, CompanySettings
from dateutil import parser
import json
import pytz

# Scopes required
SCOPES = ['https://www.googleapis.com/auth/calendar']

class CalendarService:
    def __init__(self):
        # We handle client config dynamically now
        pass
    
    def get_auth_flow(self, redirect_uri: str, client_id: str, client_secret: str):
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        return flow

    def get_authorization_url(self, redirect_uri: str, client_id: str, client_secret: str, state: str = None):
        if not client_id or not client_secret:
            raise Exception("Missing Google Client ID or Secret")
            
        flow = self.get_auth_flow(redirect_uri, client_id, client_secret)
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent' # Force consent to get refresh token
        )
        return authorization_url

    def fetch_token(self, redirect_uri: str, client_id: str, client_secret: str, code: str) -> Dict:
        if not client_id or not client_secret:
             raise Exception("Missing Google Client ID or Secret")

        flow = self.get_auth_flow(redirect_uri, client_id, client_secret)
        flow.fetch_token(code=code)
        return {
            "token": flow.credentials.token,
            "refresh_token": flow.credentials.refresh_token,
            "token_uri": flow.credentials.token_uri,
            "client_id": flow.credentials.client_id,
            "client_secret": flow.credentials.client_secret,
            "scopes": flow.credentials.scopes
        }

    def get_credentials(self, config: AppointmentConfig, db: Session = None) -> Optional[Credentials]:
        if not config.google_refresh_token:
            return None
            
        # Try to use config credentials first, then env fallback
        client_id = config.google_client_id or os.getenv("GOOGLE_CLIENT_ID")
        client_secret = config.google_client_secret or os.getenv("GOOGLE_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            return None

        creds = Credentials(
            token=config.google_access_token,
            refresh_token=config.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES
        )
        
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Update DB with new access token
                if db:
                    db_config = db.get(AppointmentConfig, config.id)
                    if db_config:
                        db_config.google_access_token = creds.token
                        db.add(db_config)
                        db.commit()
                else:
                    with Session(engine) as session:
                        db_config = session.get(AppointmentConfig, config.id)
                        if db_config:
                            db_config.google_access_token = creds.token
                            session.add(db_config)
                            session.commit()
            except Exception as e:
                print(f"Error refreshing token: {e}")
                return None
                
        return creds

    def list_events(self, config: AppointmentConfig, start_time: datetime.datetime, end_time: datetime.datetime, db: Session = None):
        """
        List events from Google Calendar.
        :param db: Optional session to reuse for token update.
        """
        with open('calendar_debug.log', 'a') as f:
            f.write(f"\n[{datetime.datetime.now()}] Listing events: {start_time} to {end_time}\n")
            f.write(f"Config: ID={config.id}, GID={config.google_calendar_id}\n")
            
        creds = self.get_credentials(config, db=db)
        if not creds:
            with open('calendar_debug.log', 'a') as f: f.write("No credentials found\n")
            return []
            
        try:
            # Ensure UTC and standard ISO format with Z
            if start_time.tzinfo is None:
                start_time = pytz.UTC.localize(start_time)
            else:
                start_time = start_time.astimezone(pytz.UTC)
                
            if end_time.tzinfo is None:
                end_time = pytz.UTC.localize(end_time)
            else:
                end_time = end_time.astimezone(pytz.UTC)

            t_min = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            t_max = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            with open('calendar_debug.log', 'a') as f: f.write(f"Querying GCal: {t_min} to {t_max}\n")

            service = build('calendar', 'v3', credentials=creds, static_discovery=False)
            
            # Using custom request with timeout if possible or relying on default client transport
            # Simple list call
            events_result = service.events().list(
                calendarId=config.google_calendar_id or 'primary', 
                timeMin=t_min,
                timeMax=t_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute(num_retries=2)
            
            items = events_result.get('items', [])
            with open('calendar_debug.log', 'a') as f: f.write(f"Found {len(items)} items\n")
            return items
        except Exception as e:
            with open('calendar_debug.log', 'a') as f: f.write(f"Error listing events: {str(e)}\n")
            print(f"Error listing events: {e}")
            return []

    def create_event(self, config: AppointmentConfig, start_time: datetime.datetime, end_time: datetime.datetime, summary: str, description: str, attendee_email: str = None):
        creds = self.get_credentials(config)
        if not creds:
            return None
            
        try:
            service = build('calendar', 'v3', credentials=creds)
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': config.timezone,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': config.timezone,
                },
            }
            if attendee_email:
                event['attendees'] = [{'email': attendee_email}]
                
            event = service.events().insert(calendarId=config.google_calendar_id, body=event).execute()
            return event
        except Exception as e:
            print(f"Error creating event: {e}")
            return None

    def delete_event(self, config: AppointmentConfig, event_id: str):
        creds = self.get_credentials(config)
        if not creds:
            return False
        try:
            service = build('calendar', 'v3', credentials=creds)
            service.events().delete(calendarId=config.google_calendar_id, eventId=event_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting event {event_id}: {e}")
            return False

    def get_available_slots(self, config_id: int, date_str: str) -> List[str]:
        """
        Calculates available slots for a specific date (YYYY-MM-DD).
        """
        """
        Calculates available slots for a specific date (YYYY-MM-DD).
        """
        with Session(engine) as session:
            config = session.get(AppointmentConfig, config_id)
            if not config:
                return []

            # Parse date and set timezone
            try:
                tz = pytz.timezone(config.timezone) if config.timezone else pytz.UTC
                target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception as e:
                print(f"Error parsing date or timezone: {e}")
                return []
                
            # Get working hours for this day
            days_map = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun'}
            day_key = days_map[target_date.weekday()]
            
            if not config.working_hours or day_key not in config.working_hours:
                return [] 
            
            time_ranges = config.working_hours[day_key] # e.g. ["09:00-12:00", "14:00-18:00"]
            if not time_ranges:
                return []

            try:
                # Correctly localize
                try:
                    day_start_dt = tz.localize(datetime.datetime.combine(target_date, datetime.time.min))
                    day_end_dt = tz.localize(datetime.datetime.combine(target_date, datetime.time.max))
                except ValueError:
                    day_start_dt = tz.localize(datetime.datetime.combine(target_date, datetime.time.min), is_dst=False)
                    day_end_dt = tz.localize(datetime.datetime.combine(target_date, datetime.time.max), is_dst=False)
            except Exception as e:
                print(f"Error checking availability: {e}")
                return []

            # 1. Get Google Events (Busy)
            try:
                # Convert to UTC for Google API to avoid format issues
                g_start = day_start_dt.astimezone(datetime.timezone.utc)
                g_end = day_end_dt.astimezone(datetime.timezone.utc)
                google_events = self.list_events(config, g_start, g_end)
            except Exception as e:
                print(f"[ERROR] Failed to fetch Google Events: {e}")
                google_events = []
            
            busy_periods = []
            for event in google_events:
                start = event['start'].get('dateTime') or event['start'].get('date') # Support full day
                end = event['end'].get('dateTime') or event['end'].get('date')
                
                if start and end:
                    # Parse and normalize to config timezone
                    s_dt = parser.parse(start)
                    e_dt = parser.parse(end)
                    
                    # Handle full day events (date only, no time)
                    if len(start) == 10: 
                        s_dt = tz.localize(datetime.datetime.combine(s_dt.date(), datetime.time.min))
                        e_dt = tz.localize(datetime.datetime.combine(e_dt.date(), datetime.time.max))
                    
                    if s_dt.tzinfo is None: s_dt = tz.localize(s_dt)
                    else: s_dt = s_dt.astimezone(tz)
                        
                    if e_dt.tzinfo is None: e_dt = tz.localize(e_dt)
                    else: e_dt = e_dt.astimezone(tz)
                    
                    busy_periods.append((s_dt, e_dt))

            # 2. Get Internal Appointments (Busy)
            from app.models import Appointment
            try:
                stmt = select(Appointment).where(
                    Appointment.company_id == config.company_id,
                    Appointment.start_time >= day_start_dt,
                    Appointment.end_time <= day_end_dt,
                    Appointment.status != 'cancelled'
                )
                internal_appts = session.exec(stmt).all()
    
                for appt in internal_appts:
                    # Ensure timezone awareness
                    s_dt = appt.start_time
                    e_dt = appt.end_time
                    
                    if s_dt.tzinfo is None: 
                         # Assuming DB stores UTC
                         s_dt = pytz.utc.localize(s_dt).astimezone(tz)
                    else: 
                        s_dt = s_dt.astimezone(tz)
                    
                    if e_dt.tzinfo is None: 
                        e_dt = pytz.utc.localize(e_dt).astimezone(tz)
                    else: 
                        e_dt = e_dt.astimezone(tz)
                    
                    busy_periods.append((s_dt, e_dt))

            except Exception as e:
                print(f"[ERROR] Failed to fetch Internal Appointments: {e}")

            # 3. Generate Slots
            available_slots = []
            slot_duration = datetime.timedelta(minutes=config.slot_duration)
            gap_duration = datetime.timedelta(minutes=config.gap_between_slots or 0)
            total_duration = slot_duration + gap_duration
            now = datetime.datetime.now(tz)
            
            for time_range in time_ranges:
                try:
                    start_str, end_str = time_range.split('-')
                    # Parse "HH:MM"
                    sh, sm = map(int, start_str.split(':'))
                    eh, em = map(int, end_str.split(':'))
                    
                    # CORRECT WAY: Use localize
                    range_start = tz.localize(datetime.datetime.combine(target_date, datetime.time(sh, sm)))
                    range_end = tz.localize(datetime.datetime.combine(target_date, datetime.time(eh, em)))
                    
                    current_slot = range_start
                    while current_slot + slot_duration <= range_end:
                        slot_end = current_slot + slot_duration
                        
                        # Filter past slots if today
                        if current_slot < now:
                            current_slot += total_duration
                            continue
                            
                        # Check collision
                        is_busy = False
                        for b_start, b_end in busy_periods:
                            # Strict overlap Check: (StartA < EndB) and (EndA > StartB)
                            if current_slot < b_end and slot_end > b_start:
                                is_busy = True
                                break
                        
                        if not is_busy:
                            available_slots.append(current_slot.isoformat())
                            
                        current_slot += total_duration
                        
                except Exception as e:
                    print(f"Error processing range {time_range}: {e}")
                    continue

            return available_slots
            


calendar_service = CalendarService()
