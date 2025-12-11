import asyncio
from app.database import engine, Base
from app.models import User, Product, Service

# Este script se puede ejecutar para crear tablas directamente sin alembic si es necesario
# python -m app.init_db

def init_db():
    print("Creando tablas de base de datos...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas.")

if __name__ == "__main__":
    init_db()
