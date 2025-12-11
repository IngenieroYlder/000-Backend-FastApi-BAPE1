# Guía Maestra de Despliegue en Easypanel (VPS)

Esta guía documenta el **proceso exacto y probado** para desplegar el Backend BAPE en Easypanel, incluyendo las soluciones a problemas de compatibilidad y puertos.

## 1. Preparación Local (Antes de subir)

### A. Dependencias Críticas (`requirements.txt`)
Para evitar errores de compatibilidad en el servidor (como el de `passlib` vs `bcrypt`), tu archivo `requirements.txt` debe tener versiones fijas:

```text
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
alembic
python-jose[cryptography]
passlib[bcrypt]==1.7.4  <-- IMPORTANTE
bcrypt==4.0.1           <-- IMPORTANTE (Versiones nuevas rompen el login)
python-dotenv
jinja2
python-multipart
email-validator
```

### B. Git
Tu proyecto debe estar en un repositorio (GitHub/GitLab).
1.  `git add .`
2.  `git commit -m "Mensaje"`
3.  `git push origin master`

---

## 2. Configuración en Easypanel

### A. Crear los Servicios
Necesitas dos servicios separados en tu proyecto de Easypanel:
1.  **Base de Datos**: Tipo `PostgreSQL` (versión 15 o similar).
2.  **Aplicación Web**: Tipo `App` (Conecta tu repositorio de GitHub).

### B. Configurar la App (Backend)
En el servicio de tu App, ve a la pestaña **Environment (Variables de Entorno)** y configura:

```ini
# Conexión a la BD (Copia estos datos de tu servicio Postgres en Easypanel)
POSTGRES_HOST=nombre_interno_servicio_db  (ej: n8n_bape)
POSTGRES_PORT=5432
POSTGRES_USER=tu_usuario_db
POSTGRES_PASSWORD=tu_contraseña_db
POSTGRES_DB=BAPE_BD

# Seguridad
SECRET_KEY=tu_clave_secreta_inventada

# Puerto (Opcional, pero buena práctica)
PORT=80
```

### C. El Comando de Inicio (CRÍTICO) ⚠️
Por defecto, Dockerfile usa el puerto 8000, pero **Easypanel espera tráffico en el puerto 80** para el proxy SSL.
Debes ir a la pestaña **General** -> **Build / Run Command** y sobrescribir el comando:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 80
```
*Sin esto, recibirás errores de "Service not reachable" o "502 Bad Gateway".*

---

## 3. Primer Despliegue e Inicialización

1.  Dale al botón **"Deploy" (Implementar)**.
2.  Espera a que salga el check verde (Running).

### Inicializar Base de Datos (Solo la primera vez)
La base de datos se crea vacía. Debes crear las tablas y el usuario administrador manualmente.

1.  Ve a la pestaña **Console** de tu servicio App.
2.  **Crear Tablas**: Ejecuta el comando de migraciones.
    ```bash
    alembic upgrade head
    ```
    *Si falla o no hace nada, usa el plan B: `python -m app.init_db`*

3.  **Crear Admin**: Ejecuta el script de creación.
    ```bash
    python create_admin.py
    ```
    *(Crea usuario: admin@bape.com / contraseña: admin)*

---

## 4. Flujo de Trabajo (Actualizaciones)

Cada vez que quieras modificar el código:

1.  **En tu PC local**:
    *   Edita tu código.
    *   Guarda cambios: `git commit -am "Nueva funcionalidad"`
    *   Sube cambios: `git push`
2.  **En Easypanel**:
    *   Ve a tu servicio App.
    *   Presiona **"Deploy"**.

Easypanel descargará el nuevo código, reconstruirá el contenedor y reiniciará el servicio sin perder tus datos de la base de datos (porque está en otro servicio).

### Solución de Problemas Comunes

*   **Error "users relation does not exist"**: No has ejecutado las migraciones. Ve al paso 3.
*   **Login Error (bcrypt/passlib)**: Revisa que `requirements.txt` tenga `bcrypt==4.0.1` y reconstruye.
*   **Service not reachable**: Revisa que el comando de inicio use `--port 80`.
