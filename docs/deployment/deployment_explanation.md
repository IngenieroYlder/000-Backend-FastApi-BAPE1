# Guía de Despliegue a Hostinger VPS y Base de Datos

Esta guía responde a tus dudas específicas sobre cómo llevar tu trabajo local al VPS.

## 1. ¿Cómo "exporto" mi contenedor al VPS?

En Docker, **no se suele exportar el contenedor activo**. Lo que hacemos es llevar el **plano de construcción** (tu código + `Dockerfile`) al servidor y construirlo allí, o llevar la **imágen empaquetada**.

### Método Recomendado: Git + Build en VPS (Más fácil)
Es el método estándar y más sencillo.

1.  **Sube tu código a GitHub/GitLab**.
2.  **Entra a tu VPS** (por SSH o terminal web).
3.  **Clona tu repositorio**: `git clone https://github.com/tu-usuario/tu-repo.git`
4.  **Entra a la carpeta** y ejecuta el mismo comando que usaste aquí:
    ```bash
    docker compose up -d --build
    ```
    *Docker leerá tu `docker-compose.yml` y construirá todo idéntico a tu local.*

### Método Alternativo: Docker Registry (Docker Hub)
Si no quieres subir código fuente al VPS:
1.  Creas la imagen en tu PC: `docker build -t tu-usuario/bape-backend .`
2.  La subes a la nube: `docker push tu-usuario/bape-backend`
3.  En el VPS solo descargas la imagen: `docker run tu-usuario/bape-backend`

---

## 2. ¿Debo crear un servicio de PostgreSQL en Hostinger?

Tienes dos opciones excelentes, depende de qué prefieras:

### Opción A: Usar la Base de Datos DE DOCKER (La que ya configuramos) ✅ *Recomendada para empezar*
En tu archivo `docker-compose.yml` ya definimos un servicio `db` (PostgreSQL).

*   **Ventaja**: Es **idéntico** a tu entorno local. No tienes que configurar nada extra en Hostinger. Al correr `docker compose up`, la base de datos se crea sola.
*   **Desventaja**: Tú eres responsable de los backups (los datos viven en el volumen `postgres_data` dentro del VPS).
*   **Cómo usarlo**: Solo sube tu `docker-compose.yml` tal cual está.

### Opción B: Usar Base de Datos MANAGED de Hostinger (Externa)
 Hostinger ofrece bases de datos PostgreSQL como servicio independiente.

*   **Ventaja**: Hostinger hace los backups, seguridad y actualizaciones por ti. Es más robusto para producción seria.
*   **Desventaja**: Cuesta dinero extra (usualmente) y requiere configuración.
*   **Cómo usarlo**:
    1.  Creas la BD en el panel de Hostinger. Te darán credenciales: `Host`, `Usuario`, `Password`, `Database Name`.
    2.  En tu VPS, editas el archivo `.env` (o las variables de entorno del contenedor) para apuntar a esa BD externa en lugar de a `db`:
        ```ini
        POSTGRES_HOST=postgres.hostinger.com  <-- El host que te den
        POSTGRES_USER=usuario_hostinger
        POSTGRES_PASSWORD=password_hostinger
        ```
    3.  En tu `docker-compose.yml` del VPS, **borras** la sección `services: db` porque ya no la necesitas.

## Resumen
Para iniciar rápido y sin complicaciones: **Usa la Opción A (Todo en Docker)** por ahora. Cuando tengas muchos usuarios reales, puedes migrar los datos a la Opción B.
