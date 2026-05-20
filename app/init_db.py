from sqlmodel import SQLModel
from app.database import engine
import app.models  # noqa: F401  registra todos los modelos en SQLModel.metadata

# Este script se puede ejecutar para crear tablas directamente sin alembic si es necesario
# python -m app.init_db

def init_db():
    print("Creando tablas de base de datos...")
    SQLModel.metadata.create_all(engine)
    print("Tablas creadas.")

if __name__ == "__main__":
    init_db()
