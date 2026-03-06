# Plan de Migración y Desarrollo: Proyecto BAPE (Bot Asistente Personal y Empresarial)

Este documento detalla el plan estratégico y técnico para migrar tu actual aplicación de chatbots (actualmente en Node.js/Express con Baileys) a una arquitectura robusta y escalable utilizando **FastAPI (Python)** y **PostgreSQL**.

El objetivo es clonar la funcionalidad actual (Login, Multi-tenancy/SaaS, WhatsApp, Telegram, OpenAI) evitando los errores del pasado y preparando el terreno para futuras integraciones con OpenClaw.

---

## 1. Arquitectura del Sistema

Al cambiar de Node.js a Python, la mayor diferencia técnica reside en la integración con **Baileys**. Baileys es una librería exclusiva de JavaScript. No existe un equivalente directo 1:1 en Python que sea tan estable para la API "no oficial" (MD).

**Estrategia Recomendada: Arquitectura Híbrida (Core Python + Motor Baileys)**

Para no perder la estabilidad ni la lógica que ya tienes con Baileys:
1.  **Backend Principal (BAPE Core)**: Implementado en **FastAPI**. Maneja la lógica de negocio, base de datos, usuarios, empresas, Telegram, OpenAI y la API REST.
2.  **Motor WhatsApp (Baileys Engine)**: Un microservicio ligero en **Node.js** (basado en tú código actual) que se encarga *exclusivamente* de la conexión con WhatsApp.
    *   Se comunica con FastAPI mediante **HTTP Webhooks** (para mensajes entrantes) y **API Local** (para enviar mensajes).
    *   FastAPI "controla" este motor (iniciar sesión, cerrar sesión, ver QR).

### Diagrama Conceptual

```mermaid
graph TD
    User[Usuario/Admin] -->|HTTPS| FastAPI[BAPE Core (FastAPI)]
    FastAPI -->|SQL| DB[(PostgreSQL)]
    FastAPI -->|Python SDK| Telegram[Telegram API]
    FastAPI -->|Python SDK| OpenAI[OpenAI API]
    
    subgraph "Integración WhatsApp"
        FastAPI <-->|HTTP/Socket| Baileys[Motor Baileys (Node.js)]
        Baileys <-->|WS| WA[WhatsApp Servers]
    end
```

---

## 2. Experiencia de Usuario y Funcionalidades (Manual de Operación)

Este sistema **BAPE** no es solo un chat, es una plataforma integral de atención al cliente automatizada. A continuación, se detalla el flujo de trabajo para una empresa cliente.

### 2.1 Conexión de Canales (El Primer Paso)
El usuario puede conectar sus canales de comunicación:
*   **Telegram**: Simplemente ingresando el Token del BotFather.
*   **WhatsApp (Dos Opciones)**:
    1.  **API Oficial (Recomendado)**: Estable, segura y aprobada por Meta. Requiere verificación de negocio.
    2.  **Escaneo QR (Baileys/Legacy)**: Permite conectar cualquier número existente escaneando un QR.
        > **⚠️ Descargo de Responsabilidad (Disclaimer)**: Esta conexión usa ingeniería inversa. Es inestable ante actualizaciones de WhatsApp y conlleva riesgos de bloqueo por parte de Meta si se detecta spam. **Se recomienda encarecidamente la API Oficial para líneas críticas.**

### 2.2 Configuración del "Cerebro" (IA)
Una vez conectado, la empresa configura cómo piensa su bot:
*   **Prompt del Sistema**: "Eres un asistente de ventas experto en zapatos...".
*   **Base de Conocimiento Multimedia**: El usuario puede cargar PDFs, TXTs o Imágenes (ej. Catálogos, Menús) y "adjuntarlos" al contexto del bot. El bot "verá" estas imágenes y leerá los documentos para responder con precisión.

### 2.3 Gestión de Equipo (Agentes Humanos)
El bot no trabaja solo. La empresa puede crear **Agentes**:
*   Darles acceso restringido (solo ver chats, o también responder).
*   Asignarles departamentos o líneas específicas.

### 2.4 Modo Híbrido (Intervención Manual)
El superpoder de BAPE es la colaboración Bot + Humano:
*   El bot responde el 80% de las dudas comunes.
*   **Intervención**: Si un agente ve que el bot se complica o el cliente pide un humano, puede activar el **"Modo Manual"** o simplemente escribir en el chat. El bot se pausa automáticamente para ese usuario o coexiste según la configuración.

### 2.5 Filtros y Segmentación
No todos merecen atención automática. La empresa puede configurar:
*   **Listas Negras**: Números a ignorar.
*   **Filtros de Grupo**: Decidir si el bot responde en grupos de WhatsApp o solo chats privados.
*   **Activación Selectiva**: "Activar bot solo fuera de horario laboral" (Futuro).

### 2.6 Métricas y Reportes
Un dashboard visual ("bonito") para la toma de decisiones:
*   **Conversaciones Totales vs Atendidas por IA**.
*   **Costo de Operación**: Consumo de tokens OpenAI.
*   **Análisis de Sentimiento**: ¿Los clientes están felices o enojados?

---

## 3. Arquitectura del Sistema

Organiza tu proyecto FastAPI siguiendo las mejores prácticas para escalabilidad (Clean Architecture simplificada).

```text
bape_backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py        # Login, Registro
│   │   │   │   ├── companies.py   # Gestión SaaS
│   │   │   │   ├── bots.py        # Configuración de Bots
│   │   │   │   └── webhooks.py    # Recibe datos de Baileys/Telegram
│   │   │   └── api.py
│   │   └── deps.py                # Dependencias (Current User, DB Session)
│   ├── core/
│   │   ├── config.py              # Variables de entorno (.env)
│   │   └── security.py            # Hashing passwords, JWT
│   ├── db/
│   │   ├── base.py
│   │   └── session.py             # Conexión Async con SQLAlchemy/SQLModel
│   ├── models/                    # Definición de Tablas (SQLModel)
│   │   ├── user.py
│   │   ├── company.py
│   │   ├── message.py
│   │   └── ...
│   ├── schemas/                   # Pydantic Models (Request/Response)
│   ├── services/
│   │   ├── openai_service.py
│   │   ├── telegram_service.py
│   │   ├── whatsapp_bridge.py     # Cliente para hablar con el Motor Baileys
│   │   └── bot_logic.py           # Lógica central del chatbot (Cerebro)
│   └── main.py
├── alembic/                       # Migraciones de BD
├── requirements.txt
└── .env
```

---

## 3. Base de Datos (PostgreSQL)

Usaremos **SQLModel** (que combina SQLAlchemy y Pydantic) para una definición limpia.
**Sí, TODOS los modelos actuales se migrarán**. He analizado tu carpeta `models/` y aquí está el mapeo:

### Tablas Principales (Mapping Completo)

1.  **Entidades Core (SaaS)**:
    *   `Company`: La entidad principal para el multi-tenancy.
    *   `User`: Usuarios del sistema (agentes, admins), vinculados a `Company`.
    *   `Plan`: Para la gestión de suscripciones y límites.
    *   `Setting`: Configuración específica por empresa (Tokens, Prompts, etc.).

2.  **Operación de Chat**:
    *   `Contact`: Clientes/Usuarios que escriben al bot.
    *   `Message`: Historial de conversaciones (Text, Image, Audio).
    *   `ActiveSession`: Control de sesiones de chat en vivo.
    *   `Session` (WhatsApp): Estado de la conexión de Baileys.

3.  **Gestión de Contenido y Archivos**:
    *   `Folder` & `Asset`: Para la gestión de archivos multimedia y documentos del bot.
    *   `UsageLog`: Registro de consumo de tokens/mensajes.
    *   `Summary`: Resúmenes de conversaciones generados por IA.
    *   `SettingsBackup`: Respaldos de configuración.

Toda esta estructura se replicará en PostgreSQL utilizando relaciones (Foreign Keys) estrictas para garantizar la integridad de los datos.

---

## 4. Autenticación, Roles y Seguridad (SaaS)

Esta es la parte **CRÍTICA**. Usaremos un sistema de permisos jerárquico y **aislamiento estricto de datos** para que *nunca* se mezclen datos entre empresas.

### 4.1 Estrategia de Roles

1.  **Superadmin (Dios)**:
    *   Tiene acceso global.
    *   Puede ver, crear y suspender *cualquier* Empresa.
    *   Gestiona planes y facturación.
2.  **Company Admin (Admin de Empresa)**:
    *   Solo ve datos de SU `company_id`.
    *   Puede crear y gestionar a sus propios Agentes.
    *   Configura los bots de su empresa.
    *   Ve todas las conversaciones de su empresa.
3.  **Agent (Colaborador)**:
    *   Solo ve datos de SU `company_id`.
    *   Acceso restringido: Solo puede ver/responder conversaciones asignadas (o todas, según config de la empresa).
    *   No puede tocar configuraciones sensibles (API Keys, Facturación).

### 4.2 Seguridad Técnica (FastAPI Dependencies)

Implementaremos "Guardianes" (Dependencies) que se ejecutan antes de cada endpoint:

*   **`get_current_active_user`**: Valida el JWT. Si expiró o es inválido -> Error 401.
*   **`get_current_company`**: Extrae el `company_id` del usuario. Inyecta este ID automáticamente en las consultas a BD.
    *   *Ejemplo*: Si el usuario es de la empresa A, y pide "listar mensajes", el sistema internamente hace `SELECT * FROM messages WHERE company_id = 'A'`. Es **imposible** que vea datos de la empresa B.
*   **`check_role(['admin'])`**: Un decorador para rutas sensibles. Si un Agente intenta entrar a "Configuración de Pagos", el sistema lo rechaza automáticamente (Error 403 Forbidden).

### 4.3 JWT (El Token)

El token JWT contendrá de forma encriptada:
*   `sub`: ID del Usuario.
*   `company_id`: ID de su Empresa.
*   `role`: Su rol actual.
*   `exp`: Expiración (para seguridad).

Esto garantiza que cada petición lleve la "identidad" completa y segura del usuario.

---

## 5. Integración WhatsApp (El "Baileys Engine")

Para esta fase, crearás una carpeta `baileys_engine/` dentro o fuera del proyecto principal.

1.  **Código Node.js**: Copia tu `baileysService.js` actual, pero elimina la dependencia de la base de datos directa.
2.  **API Interna**:
    *   Crea un servidor Express simple en este engine.
    *   `POST /init-session`: Recibe `{ company_id, session_name }`. Inicia Baileys.
    *   `POST /send-message`: Recibe `{ to, text, media }`. Usa la sesión activa para enviar.
    *   **Webhooks**: Cuando Baileys reciba un mensaje, hará un `POST http://localhost:8000/api/v1/webhooks/whatsapp` enviando el JSON del mensaje a tu FastAPI.
3.  **Ventaja**: Si Baileys falla o necesita actualización (muy común), solo tocas el microservicio Node.js; tu lógica de negocio en Python no se rompe.

---

## 6. Integración Telegram y OpenAI (Nativo Python)

Aquí Python brilla.

1.  **Telegram**: Usa `python-telegram-bot` en modo asíncrono.
    *   Puedes usar `ApplicationBuilder` para levantar bots dinámicamente según los tokens guardados en la BD de PostgreSQL.
2.  **OpenAI**:
    *   Usa la librería oficial `openai`.
    *   Implementa la lógica de Transcripción (Whisper) y Chat (GPT-4o) en `services/openai_service.py`.

---

## 8. Frontend & Dashboard (React/Vite)

Para cumplir con el requerimiento de **clonar la funcionalidad actual** (Login, Paneles, Gráficas, Chat), migraremos el frontend actual a una estructura más limpia y moderna, conectándola con FastAPI.

### Stack Tecnológico
*   **Framework**: React con Vite (Rápido y ligero).
*   **Estilos**: Tailwind CSS (Para una estética moderna y premium).
*   **Estado**: Bustand o Context API (Para manejar la sesión del usuario y websockets).
*   **Gráficas**: Recharts o Chart.js (Para las métricas del Dashboard).

### Módulos a Migrar/Clonar
1.  **Autenticación**:
    *   `Login`: Formulario con validación y manejo de errores.
    *   `Registro`: Habilitado/Deshabilitado según configuración (SaaS).
    *   `Recuperar Contraseña`.
2.  **Dashboard Principal (Home)**:
    *   **Tarjetas de Resumen**: Total Mensajes, Sesiones Activas, Uso de OpenAI.
    *   **Gráficas**: Actividad diaria/mensual, Tipos de mensajes (Texto vs Audio).
    *   **Estado de Bots**: Lista de conexiones activas (WhatsApp/Telegram) con indicadores de estado en tiempo real.
3.  **Módulo de Chat (Inbox)**:
    *   Clon de la interfaz tipo WhatsApp Web.
    *   Lista de contactos a la izquierda (con buscador y filtros).
    *   Ventana de chat a la derecha (mensajes en tiempo real vía WebSocket).
    *   Soporte multimedia (audios, imágenes).
4.  **Configuración de Bots**:
    *   **WhatsApp**: Generador de QR, Botón de desconexión.
    *   **Telegram**: Input para Token del Bot.
    *   **OpenAI**: Configuración de Prompts del sistema y selección de modelo.
5.  **Gestión SaaS (Superadmin)**:
    *   Tabla CRUD de Empresas (Crear, Editar, Suspender).
    *   Asignación de límites (slots de bots) y planes.

---

## 9. Fase Opcional: OpenClaw + Calendario

Una vez que el sistema BAPE esté estable (Login, Chat, WhatsApp/Telegram funcionando), puedes integrar la "Super Inteligencia":

1.  **OpenClaw**: Es un agente autónomo. Puedes ejecutarlo como un servicio separado (Docker).
2.  **Integración**:
    *   BAPE puede exponer una API para que OpenClaw "lea" el historial de chat o "envíe" mensajes.
    *   Herramientas (Tools) para OpenClaw: Dale acceso a tu BD para agendar citas.
3.  **Google Calendar**:
    *   Usa la API de Google Calendar en Python.
    *   Crea una "Tool" para OpenClaw: `check_availability(date)` y `create_event(date, email)`.
    *   Cuando el usuario pida una cita en WhatsApp, BAPE se lo pasa a OpenClaw -> OpenClaw consulta Calendar -> OpenClaw responde confirmación.

---

## Checklist para el Éxito

1.  [ ] **Setup**: Iniciar entorno Python, Instalar FastAPI, SQLModel, PostgreSQL driver (`asyncpg`).
2.  [ ] **BD**: Definir modelos User y Company. Crear migración inicial con Alembic.
3.  [ ] **Auth**: Implementar Login y Registro (solo Superadmin puede crear empresas).
4.  [ ] **Baileys Engine**: Extraer el código de `baileysService.js` a un servicio Node independiente.
5.  [ ] **Webhook Handler**: Crear endpoint en FastAPI para recibir mensajes de Baileys.
6.  [ ] **Bot Logic**: Traducir `botLogic.js` a Python.
7.  [ ] **Frontend**: Clonar tu UI actual, apuntando a los nuevos endpoints de FastAPI.

Este plan asegura que mantienes la funcionalidad crítica de WhatsApp (Baileys) mientras aprovechas la potencia y orden de Python/FastAPI para el crecimiento futuro.
