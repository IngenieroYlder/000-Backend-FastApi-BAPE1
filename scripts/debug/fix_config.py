from sqlmodel import Session, select
from app.database import engine
from app.models import AppointmentConfig

def update_config():
    with Session(engine) as session:
        # Fetch config
        stmt = select(AppointmentConfig).where(AppointmentConfig.id == 1)
        config = session.exec(stmt).first()
        
        if config:
            print(f"Current Working Hours: {config.working_hours}")
            
            # Add Thursday
            new_hours = config.working_hours.copy()
            new_hours['thu'] = ['09:00-18:00']
            config.working_hours = new_hours
            
            session.add(config)
            session.commit()
            print(f"Updated Working Hours: {config.working_hours}")
        else:
            print("Config not found.")

if __name__ == "__main__":
    update_config()
