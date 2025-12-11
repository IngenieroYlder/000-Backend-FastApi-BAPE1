# Backend FastAPI BAPE - Documentación

Este proyecto es un backend en FastAPI con base de datos PostgreSQL, autenticación JWT y un frontend básico integrado.

## Estructura del Proyecto

```
/
├── app/
│   ├── main.py            # Punto de entrada
│   ├── database.py        # Conexión BD
│   ├── models.py          # Modelos SQLAlchemy
│   ├── schemas.py         # Esquemas Pydantic
│   ├── auth.py            # Lógica JWT
│   ├── init_db.py         # Script inicialización BD
│   ├── routers/           # Rutas API
│   └── templates/         # Vistas HTML (Login, Dashboard)
├── alembic/               # Migraciones
├── alembic.ini            # Config Alembic
├── Dockerfile             # Config Docker
├── requirements.txt       # Dependencias
└── .env                   # Variables de entorno
```

## Configuración y Ejecución Local

1. **Prerrequisitos**: Python 3.11+ y PostgreSQL corriendo.
2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configurar Entornoo**:
   - Edita el archivo `.env` si es necesario (por defecto apunta a `localhost` o valores de docker).
4. **Inicializar Base de Datos**:
   - Opción rápida (crea tablas directamente):
     ```bash
     python -m app.init_db
     ```
   - Opción recomendada (Alembic):
     ```bash
     alembic revision --autogenerate -m "Initial migration"
     alembic upgrade head
     ```
5. **Ejecutar Servidor**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
6. **Acceder**:
   - Abre `http://localhost:8000/login` en tu navegador.
   - **Nota**: Para el primer ingreso, debes crear un usuario mediante la API (POST `/auth/register`) usando Postman o cURL, ya que el login solo permite ingresar usuarios existentes.
     ```bash
     curl -X POST "http://localhost:8000/auth/register" -H "Content-Type: application/json" -d '{"email": "admin@example.com", "password": "admin"}'
     ```

## Despliegue en VPS con Docker (Easypanel)

### Dockerfile
El proyecto incluye un `Dockerfile` optimizado.

### Pasos Generales
1. **Subir código**: Sube este repositorio a tu VPS o Git.
2. **Construir Imagen**:
   ```bash
   docker build -t bape-backend .
   ```
3. **Ejecutar Contenedor**:
   ```bash
   docker run -d -p 8000:8000 --env-file .env --name n8n_service bape-backend
   ```

### En Easypanel
1. Crea un nuevo **App Services**.
2. Selecciona **Source** (GitHub/GitLab) o **Docker Image** si la has subido a un registro.
3. En **Build**, asegúrate de que el Dockerfile sea detectado.
4. En **Environment**:
   - Copia el contenido de `.env`.
   - Asegúrate de que `POSTGRES_HOST` apunte a tu servicio de base de datos en Easypanel (si usas la base de datos interna de Easypanel, usa el host y credenciales que te provee).
5. **Port**: Expone el puerto `8000`.
6. **Deploy**.

## Endpoints Principales

- `POST /auth/register`: Registrar usuario.
- `POST /auth/login`: Obtener Token JWT.
- `GET /products`: Listar productos (Requiere Auth).
- `POST /products`: Crear producto (Requiere Auth).
- `GET /services`: Listar servicios (Requiere Auth).
- `GET /product-categories`: Listar categorías de productos.
- `GET /service-categories`: Listar categorías de servicios.
- `GET /login`: Ver página de login.
- `GET /dashboard`: Ver panel de administración.

## Notas Adicionales
- Se han separado las categorías en dos tablas: `product_categories` y `service_categories`.
- Se han traducido los comentarios del código a español.

