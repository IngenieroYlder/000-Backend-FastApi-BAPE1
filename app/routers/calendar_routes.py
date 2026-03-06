from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlmodel import Session, select
from app.database import get_session
from app import models, auth
from app.services.calendar_service import calendar_service
from typing import Dict, Optional
from pydantic import BaseModel, EmailStr
import os
import datetime

router = APIRouter(
    prefix="/calendar",
    tags=["Calendar"]
)

@router.get("/auth-url")
def get_auth_url(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_session)
):
    # Fetch config to check if CREDENTIALS are set
    stmt = select(models.AppointmentConfig).where(models.AppointmentConfig.company_id == current_user.company_id)
    config = db.exec(stmt).first()
    
    if not config or not config.google_client_id or not config.google_client_secret:
        raise HTTPException(status_code=400, detail="Google Client ID and Secret not configured in Settings")
    
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/calendar/callback")
    print(f"[Calendar Auth] using Redirect URI: {redirect_uri}")
    
    url = calendar_service.get_authorization_url(
        redirect_uri, 
        config.google_client_id, 
        config.google_client_secret, 
        state=str(current_user.company_id)
    )
    return {"url": url}

from fastapi.responses import RedirectResponse

@router.get("/callback")
def oauth_callback(code: str, state: str, db: Session = Depends(get_session)):
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/calendar/callback")
    
    try:
        company_id = int(state)
        # Check if config exists
        stmt = select(models.AppointmentConfig).where(models.AppointmentConfig.company_id == company_id)
        config = db.exec(stmt).first()
        
        if not config:
            raise HTTPException(status_code=400, detail="Configuration not found")

        if not config.google_client_id or not config.google_client_secret:
             raise HTTPException(status_code=400, detail="Google Client ID and Secret not configured")

        # Allow extra scopes (Drive, etc.) without error
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

        # Exchange code for tokens
        token_data = calendar_service.fetch_token(
            redirect_uri, 
            config.google_client_id.strip(), 
            config.google_client_secret.strip(), 
            code
        )
        
        config.google_access_token = token_data["token"]
        config.google_refresh_token = token_data["refresh_token"]
        # config.token_expiry = ... 
        
        db.add(config)
        db.commit()
        db.refresh(config)
        
        return RedirectResponse(url="/settings?calendar_connected=True")
        
    except Exception as e:
        print(f"[OAuth Error] {str(e)}")
        raise HTTPException(status_code=400, detail=f"OAuth Error: {str(e)}")

@router.get("/settings")
def get_settings(
    db: Session = Depends(get_session), 
    current_user: models.User = Depends(auth.get_current_user)
):
    stmt = select(models.AppointmentConfig).where(models.AppointmentConfig.company_id == current_user.company_id)
    config = db.exec(stmt).first()
    
    if not config:
        return {} # Or defaults
        
    return config

@router.post("/settings")
def update_settings(
    payload: dict = Body(...),
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user)
):
    stmt = select(models.AppointmentConfig).where(models.AppointmentConfig.company_id == current_user.company_id)
    config = db.exec(stmt).first()
    
    if not config:
        config = models.AppointmentConfig(company_id=current_user.company_id)
    
    # Update fields
    print(f"[DEBUG] update_settings payload: {payload}")
    
    if 'slot_duration' in payload:
        config.slot_duration = payload['slot_duration']
    if 'working_hours' in payload:
        config.working_hours = payload['working_hours']
    if 'timezone' in payload:
        config.timezone = payload['timezone']
    if 'google_client_id' in payload:
        config.google_client_id = payload['google_client_id']
    if 'google_client_secret' in payload:
        config.google_client_secret = payload['google_client_secret']
        
    db.add(config)
    db.commit()
    db.refresh(config)
    
    return config

# ----------------------------------------------------------------
# Pydantic Models
# ----------------------------------------------------------------
class BookingRequest(BaseModel):
    date: str # YYYY-MM-DD
    time: str # HH:MM (24h)
    customer_name: str
    customer_phone: str
    customer_email: Optional[EmailStr] = None
    notes: Optional[str] = None

# ----------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------

@router.get("/availability")
def check_availability(
    date: str, 
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Check availability for a specific date (YYYY-MM-DD).
    """
    stmt = select(models.AppointmentConfig).where(models.AppointmentConfig.company_id == current_user.company_id)
    config = db.exec(stmt).first()
    
    if not config:
        raise HTTPException(status_code=400, detail="Calendar configuration not found")
        
    slots = calendar_service.get_available_slots(config.id, date)
    return {"date": date, "available_slots": slots}

@router.post("/book")
def book_appointment(
    booking: BookingRequest,
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Book an appointment. Handles Google Calendar sync and DB record.
    """
    stmt = select(models.AppointmentConfig).where(models.AppointmentConfig.company_id == current_user.company_id)
    config = db.exec(stmt).first()
    
    if not config:
        raise HTTPException(status_code=400, detail="Calendar configuration not found")
        
    # 1. Parse Date/Time
    try:
        start_dt = datetime.datetime.strptime(f"{booking.date} {booking.time}", "%Y-%m-%d %H:%M")
        # Assume input is localized or naive-as-local. We should localize it to config timezone.
        import pytz
        tz = pytz.timezone(config.timezone) if config.timezone else pytz.UTC
        start_dt = tz.localize(start_dt)
        
        end_dt = start_dt + datetime.timedelta(minutes=config.slot_duration)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date/time format: {e}")

    # 2. Race Condition Check (Re-check availability)
    from app.models import Appointment
    stmt_overlap = select(Appointment).where(
        Appointment.company_id == current_user.company_id,
        Appointment.start_time < end_dt,
        Appointment.end_time > start_dt,
        Appointment.status != 'cancelled'
    )
    if db.exec(stmt_overlap).first():
        raise HTTPException(status_code=409, detail="Slot already booked (Internal)")

    # 3. Create Google Event
    description = f"Tel: {booking.customer_phone}\nEmail: {booking.customer_email or 'N/A'}\nNotas: {booking.notes or ''}\nGestionado por BAPE."
    g_event = calendar_service.create_event(
        config, 
        start_dt, 
        end_dt, 
        f"Cita con {booking.customer_name}", 
        description,
        booking.customer_email
    )
    
    if not g_event:
        # Fallback? No, fail.
        raise HTTPException(status_code=500, detail="Failed to create Google Calendar event")
        
    # 4. Save to DB
    new_appt = Appointment(
        company_id=current_user.company_id,
        title=f"Cita con {booking.customer_name}",
        start_time=start_dt,
        end_time=end_dt,
        client_name=booking.customer_name,
        client_phone=booking.customer_phone,
        client_email=booking.customer_email,
        status="confirmed",
        google_event_id=g_event.get('id'),
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(new_appt)
    db.commit()
    db.refresh(new_appt)
    
    return {"status": "success", "appointment_id": new_appt.id, "google_id": new_appt.google_event_id}
@router.get("/appointments")
def list_appointments(
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user)
):
    """List all appointments, merging local DB and Google Calendar events."""
    res_list = []
    
    # 1. Local Appointments
    stmt = select(models.Appointment).where(models.Appointment.company_id == current_user.company_id)
    if start:
        try:
            # Strip timezone for DB comparison if DB stores naive timestamps
            s_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00')).replace(tzinfo=None)
            stmt = stmt.where(models.Appointment.end_time >= s_dt)
        except: pass
    if end:
        try:
            e_dt = datetime.datetime.fromisoformat(end.replace('Z', '+00:00')).replace(tzinfo=None)
            stmt = stmt.where(models.Appointment.start_time <= e_dt)
        except: pass
        
    local_appts = db.exec(stmt).all()
    print(f"[Calendar Sync] Found {len(local_appts)} local appointments")
    # Convert local to list of dicts for uniformity
    for a in local_appts:
        appt_dict = a.model_dump()
        appt_dict['is_external'] = False
        res_list.append(appt_dict)
    
    # 2. Google Calendar Real-time Sync
    local_g_ids = {a.google_event_id for a in local_appts if a.google_event_id}
    print(f"[Calendar Sync] Local GCal IDs: {local_g_ids}")
    
    stmt_conf = select(models.AppointmentConfig).where(models.AppointmentConfig.company_id == current_user.company_id)
    config = db.exec(stmt_conf).first()
    
    with open('calendar_debug.log', 'a') as f:
        f.write(f"Config found: {config is not None}\n")
        if config:
            f.write(f"Has token: {config.google_refresh_token is not None}\n")
            f.write(f"Calendar ID: {config.google_calendar_id}\n")

    if config and config.google_refresh_token:
        try:
            # FullCalendar usually sends ISO strings. Ensure we have fallback if not present.
            if not start: start = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
            if not end: end = (datetime.datetime.now() + datetime.timedelta(days=7)).isoformat()
            
            g_start = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
            g_end = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
            
            from app.services.calendar_service import calendar_service
            g_events = calendar_service.list_events(config, g_start, g_end, db=db)
            
            for ge in g_events:
                ge_id = ge.get('id')
                if ge_id not in local_g_ids:
                    # External event
                    st = ge['start'].get('dateTime') or ge['start'].get('date')
                    en = ge['end'].get('dateTime') or ge['end'].get('date')
                    res_list.append({
                        "id": f"g_{ge_id}",
                        "title": ge.get('summary', '(Google Event)'),
                        "start_time": st,
                        "end_time": en,
                        "status": "confirmed",
                        "is_external": True,
                        "google_event_id": ge_id,
                        "client_name": "Externo (GCal)",
                        "client_email": ge.get('creator', {}).get('email')
                    })
        except Exception as e:
            with open('calendar_debug.log', 'a') as f:
                f.write(f"Error in list_appointments GSync: {str(e)}\n")
            print(f"[Calendar Sync Error] {str(e)}")
            
    return res_list

@router.put("/appointments/{id}")
def update_appointment(
    id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user)
):
    appt = db.get(models.Appointment, id)
    if not appt or appt.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    if 'title' in payload: appt.title = payload['title']
    if 'start_time' in payload: appt.start_time = datetime.datetime.fromisoformat(payload['start_time'].replace('Z', '+00:00'))
    if 'end_time' in payload: appt.end_time = datetime.datetime.fromisoformat(payload['end_time'].replace('Z', '+00:00'))
    if 'status' in payload: appt.status = payload['status']
    if 'client_name' in payload: appt.client_name = payload['client_name']
    if 'client_phone' in payload: appt.client_phone = payload['client_phone']
    if 'client_email' in payload: appt.client_email = payload['client_email']
    if 'contact_id' in payload: appt.contact_id = payload['contact_id']
    
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt

@router.delete("/appointments/{id}")
def delete_appointment(
    id: int,
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user)
):
    appt = db.get(models.Appointment, id)
    if not appt or appt.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Optional: Delete from Google Calendar if exists
    if appt.google_event_id:
        try:
            stmt_conf = select(models.AppointmentConfig).where(models.AppointmentConfig.company_id == current_user.company_id)
            config = db.exec(stmt_conf).first()
            if config:
                calendar_service.delete_event(config, appt.google_event_id)
        except Exception as e:
            print(f"[Calendar Error] Failed to delete GEvent: {e}")

    db.delete(appt)
    db.commit()
    return {"status": "deleted"}

@router.post("/manual-book")
def manual_book(
    payload: dict = Body(...),
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Manually book an appointment (Internal CRUD)"""
    stmt_conf = select(models.AppointmentConfig).where(models.AppointmentConfig.company_id == current_user.company_id)
    config = db.exec(stmt_conf).first()
    
    if not config:
        raise HTTPException(status_code=400, detail="Configuración de calendario no encontrada")
        
    start_dt = datetime.datetime.fromisoformat(payload['start_time'].replace('Z', '+00:00'))
    end_dt = datetime.datetime.fromisoformat(payload['end_time'].replace('Z', '+00:00'))
    
    # 1. Google Event
    g_event_id = None
    try:
        g_event = calendar_service.create_event(
            config, 
            start_dt, 
            end_dt, 
            payload.get('title', f"Cita: {payload.get('client_name')}"),
            payload.get('notes', ''),
            payload.get('client_email')
        )
        if g_event: g_event_id = g_event.get('id')
    except Exception as e:
        print(f"[Calendar Error] GSync Falló: {e}")

    # 2. Save Local
    new_appt = models.Appointment(
        company_id=current_user.company_id,
        title=payload.get('title', f"Cita: {payload.get('client_name')}"),
        start_time=start_dt,
        end_time=end_dt,
        client_name=payload.get('client_name'),
        client_phone=payload.get('client_phone'),
        client_email=payload.get('client_email'),
        contact_id=payload.get('contact_id'),
        google_event_id=g_event_id,
        status="confirmed"
    )
    db.add(new_appt)
    db.commit()
    db.refresh(new_appt)
    return new_appt

    return new_appt
