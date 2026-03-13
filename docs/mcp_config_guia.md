# Guía de Uso y Configuración: BAPE MCP Server 🤖

Esta guía explica detalladamente cómo conectar tu agentes de IA locales (como Claude Desktop o Cursor) al servidor MCP de BAPE, incluso si tu proyecto y base de datos ya están desplegados en el VPS (Hostinger/Dokploy).

---

## 🚀 Concepto Fundamental
El servidor MCP (`mcp_server.py`) debe ejecutarse en la **misma máquina** donde tienes instalado Claude Desktop o Cursor. Este script actuará como un puente entre la IA y tu base de datos en el VPS.

---

## 1. Requisitos Previos en tu Computadora Local
Asegúrate de tener lo siguiente en tu PC de Windows:
1.  **Python 3.10+** instalado.
2.  **Dependencias**: Abre una terminal en tu proyecto local y ejecuta:
    ```bash
    pip install mcp mcp[cli] sqlmodel psycopg2-binary
    ```

---

## 2. Acceso a la Base de Datos del VPS
Como tu base de datos está en un contenedor de Dokploy, no suele estar abierta al público por seguridad. Tienes dos opciones para que el MCP se conecte:

### Opción A: Exponer el puerto en Dokploy (Fácil)
1.  En el panel de Dokploy, ve a tu servicio `bape_db`.
2.  Busca la sección de **Ports**.
3.  Asegúrate de que el puerto interno `5432` esté mapeado a un puerto externo (ej. `5432`).
4.  Tu URL de conexión será: `postgresql+psycopg2://usuario:password@IP_DE_TU_VPS:5432/bape_db`

### Opción B: Túnel SSH (Recomendado/Seguro)
Si no quieres abrir puertos en el VPS, abre una terminal en tu PC y manténla abierta con este comando:
```bash
ssh -L 5433:localhost:5432 root@187.77.222.161
```
*(Esto mapea la DB del VPS a tu puerto local 5433).* Su URL de conexión sería: `postgresql+psycopg2://postgres:password@localhost:5433/bape_db`

---

## 3. Configuración en Claude Desktop
1.  Presiona `Win + R` y escribe `%APPDATA%\Claude` y abre la carpeta.
2.  Busca o crea el archivo `claude_desktop_config.json`.
3.  Pega la siguiente configuración (ajusta las rutas y credenciales):

```json
{
  "mcpServers": {
    "bape": {
      "command": "python",
      "args": [
        "C:/RUTA/A/TU/PROYECTO/mcp_server.py"
      ],
      "env": {
        "DATABASE_URL": "postgresql+psycopg2://usuario:password@IP_O_LOCALHOST:PUERTO/bape_db",
        "BAILEYS_URL": "http://IP_DE_TU_VPS:3005"
      }
    }
  }
}
```

---

## 4. ¿Qué puede hacer la IA ahora?
Una vez configurado, reinicia Claude Desktop. Verás un icono de **🔌 (BAPE)**. Ahora puedes pedirle cosas como:

*   **"Lista mis productos del catálogo BAPE"**: La IA usará el recurso `bape://catalog/products`.
*   **"Busca al cliente 'Juan' y mándale un WhatsApp diciendo que lo esperamos mañana"**: La IA buscará en la DB y luego usará la herramienta `send_whatsapp_message`.
*   **"¿Qué citas tengo programadas para hoy?"**: La IA usará `list_appointments`.
*   **"Crea una cita para el contacto ID 5 mañana a las 10 am"**: La IA usará `create_appointment_manual`.

---

## 5. Troubleshooting (Solución de problemas)
- **Error de Conexión**: Verifica que el `DATABASE_URL` sea accesible desde tu computadora. Prueba con un gestor como DBeaver primero.
- **Node Modules / Baileys**: Asegúrate de que el `BAILEYS_URL` apunte a la IP pública de tu VPS en el puerto `3005`.
- **Logs**: Si el servidor no inicia en Claude, revisa los logs de Claude en `%USERPROFILE%\AppData\Local\Logs\Claude`.

---
*Documento preparado para la entrega técnica del ecosistema BAPE.*
