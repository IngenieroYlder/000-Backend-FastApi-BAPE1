from sqlmodel import Session, select
from app.database import engine
from app.models import AppointmentConfig
from app.services.calendar_service import calendar_service
import datetime

def check_config():
    with Session(engine) as session:
        # Fetch all configs
        configs = session.exec(select(AppointmentConfig)).all()
        print(f"Found {len(configs)} AppointmentConfigs.")
        
        for config in configs:
            print(f"ID: {config.id}, Company ID: {config.company_id}")
            print(f"Working Hours: {config.working_hours}")
            print(f"Timezone: {config.timezone}")
            print(f"Slot Duration: {config.slot_duration}")
            
            # Test availability for tomorrow
            tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"\n[TESTING] Checking availability for {tomorrow} with Config ID {config.id}...")
            
            try:
                slots = calendar_service.get_available_slots(config.id, tomorrow)
                print(f"Slots returned: {slots}")
            except Exception as e:
                print(f"Error checking slots: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    check_config()
