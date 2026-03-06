# Guía de Despliegue: Seguridad y Protección de Código

## 1. ¿Clonar Repo vs. Imagen Pre-empaquetada?

### A. Clonar Repositorio (Git Clone) en VPS
*   **Proceso**: Subes código a GitHub -> Entras al VPS -> `git clone` -> `docker compose up --build`.
*   **Ventaja**: Es muy fácil de actualizar y "arreglar" cosas rápido en el servidor si hay una emergencia.
*   **Seguridad**: 🔴 **BAJA**. Tu código fuente completo (`.py`) está visible en la carpeta del servidor. Cualquiera con acceso al VPS puede copiarlo.

### B. Imagen Pre-empaquetada (Docker Hub / Registry Privado)
*   **Proceso**: Construyes en tu PC -> Subes imagen a Docker Hub (Privado) -> En VPS solo haces `docker run`.
*   **Ventaja**: El despliegue es más limpio y rápido (no instalas dependencias en el VPS, ya vienen listas).
*   **Seguridad**: 🟡 **MEDIA**. No hay una carpeta con tu código "a la vista" en el sistema de archivos del servidor.

---

## 2. El Problema del "Cliente con Acceso al VPS"

Si el VPS es del cliente y él tiene la contraseña **root** o **admin**:

> **🚨 VERDAD DURA**: Si le entregas el código en *su* servidor (incluso con Docker), técnicamente **pueden** robar tu código si tienen conocimientos técnicos medios/avanzados.

Aunque uses una Imagen Docker (Opción B), un cliente curioso podría entrar al contenedor (`docker exec -it ... bash`) y leer los archivos `.py` que están adentro.

### ¿Qué te favorece más?

1.  **Mejor Opción: SaaS (Software as a Service) 🏆**
    *   **No le des el código.** Aloja la aplicación en **TU** VPS.
    *   Cobrale una mensualidad por el uso.
    *   **Protección**: 100%. Nunca tocan tu código.

2.  **Segunda Opción: Usar Imagen Docker (Registry Privado)**
    *   Usa el método de imagen pre-empaquetada.
    *   Es más difícil para un usuario "normal" sacar el código que si estuviera en una carpeta abierta. Crea una barrera de entrada.
    *   *Nota: Recuerda que Python es un lenguaje interpretado, siempre es "legible" a menos que uses herramientas avanzadas de ofuscación (como Cython o PyArmor), pero eso complica el desarrollo.*

3.  **Si DEBES instalarlo en SU servidor:**
    *   Firma un contrato legal de Propiedad Intelectual.
    *   Cobra caro el "Setup" asumiendo que el código pasa a ser "de ellos" en cierto modo.

## Resumen: Tu Estrategia

1.  Si puedes, **alójalo tú** (Hostinger a tu nombre) y cóbrale el servicio. Es lo único 100% seguro.
2.  Si es obligatorio usar el VPS de ellos: Usa **Imágenes Docker** (Opción B).
    *   No tendrán la carpeta `src` a la vista.
    *   Es profesional y limpio.
    *   Dificulta el robo casual, aunque no detiene a un hacker decidido.
