from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import auth_routes, products_routes, services_routes, frontend_routes, categories_routes, users_routes
from app.database import engine, Base

# Crear tablas si no existen (Inicio rápido sin alembic)
# Base.metadata.create_all(bind=engine) 
# Nota: Usar alembic para migraciones en producción, pero esto es útil para desarrollo si no se ejecuta alembic manualmente

app = FastAPI(
    title="BAPE Backend",
    description="Backend FastAPI para servicio BAPE",
    version="1.0.0"
)

# Routers (Rutas)
app.include_router(auth_routes.router)
app.include_router(products_routes.router)
app.include_router(services_routes.router)
app.include_router(categories_routes.router)
app.include_router(users_routes.router)
app.include_router(frontend_routes.router)

# Si tuvieras archivos estáticos, los montarías aquí
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
def health_check():
    return {"status": "ok"}
