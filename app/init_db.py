from sqlmodel import SQLModel, Session, select
from app.database import engine
from app.models import Plan
import app.models  # noqa: F401  registra todos los modelos en SQLModel.metadata

# Este script se puede ejecutar para crear tablas directamente sin alembic si es necesario
# python -m app.init_db


def seed_default_plan():
    """Crea el Plan 'Free' por defecto si no existe."""
    with Session(engine) as s:
        existing = s.exec(select(Plan).where(Plan.name == "Free")).first()
        if existing:
            print(f"Plan 'Free' ya existe (id={existing.id}).")
            return
        plan = Plan(name="Free", price=0.0, limits={"max_users": 5, "max_bots": 1})
        s.add(plan)
        s.commit()
        s.refresh(plan)
        print(f"Plan 'Free' creado (id={plan.id}).")


def init_db():
    print("Creando tablas de base de datos...")
    SQLModel.metadata.create_all(engine)
    print("Tablas creadas.")
    seed_default_plan()


if __name__ == "__main__":
    init_db()
