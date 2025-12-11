# Guía de Despliegue con Docker (VPS)

## Prerrequisitos
1.  Servidor VPS (Ubuntu/Debian recomendado) con acceso SSH.
2.  Docker instalado en el VPS.
3.  Docker Compose instalado (opcional, pero recomendado).

## Paso 1: Preparar los Archivos
Asegúrate de tener los siguientes archivos en tu carpeta del proyecto:
- `Dockerfile`
- `requirements.txt`
- `.env` (¡No subas tus secretos a repositorios públicos!)
- Carpeta `app/`

## Paso 2: Crear el Dockerfile
Si no lo tienes, crea un archivo llamado `Dockerfile` en la raíz:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema requeridas para psycopg2 y otros
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponer el puerto
EXPOSE 8000

# Comando para iniciar la app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Paso 3: Construir la Imagen
Desde la raíz de tu proyecto, ejecuta:

```bash
docker build -t bape-backend .
```

Si estás en Windows y vas a subirlo a un VPS Linux, es mejor subir los archivos y construir allá, o usar un registro de imágenes (Docker Hub).

### Opción A: Construir directamente en el VPS
1.  Sube tus archivos al VPS (usando SCP o Git).
    ```bash
    scp -r "d:\Colombia Picture\n8n agente ia burbuja\000 Backend FastApi BAPE" usuario@tu-vps-ip:/home/usuario/bape-backend
    ```
2.  Conéctate por SSH y navega a la carpeta.
3.  Ejecuta `docker build -t bape-backend .`

## Paso 4: Ejecutar el Contenedor

Para ejecutarlo conectándose a tu base de datos PostgreSQL local (host):

```bash
docker run -d \
  --name bape-api \
  -p 8000:8000 \
  -e POSTGRES_HOST=host.docker.internal \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=admin \
  -e POSTGRES_DB=BAPE_BD \
  bape-backend
```
*Nota: `host.docker.internal` funciona en Windows/Mac. En Linux puede requerir `--add-host=host.docker.internal:host-gateway`.*

### Mejor Opción: Docker Compose (App + DB)
Crea un archivo `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=admin
      - POSTGRES_DB=BAPE_BD
    ports:
      - "5432:5432"

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_HOST=db
      - POSTGRES_PORT=5432
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=admin
      - POSTGRES_DB=BAPE_BD
      - SECRET_KEY=tu_clave_secreta_super_segura
    depends_on:
      - db

volumes:
  postgres_data:
```

Para correr todo:
```bash
docker-compose up -d --build
```

## Paso 5: Verificar
Visita `http://<tu-vps-ip>:8000/docs` para ver la documentación automática de Swagger y verificar que el servidor está corriendo.
