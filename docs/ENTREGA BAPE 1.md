# DOCUMENTO DE ENTREGA: PROYECTO BAPE

Este documento detalla la arquitectura de software, la navegación del sistema y la pila tecnológica utilizada en el desarrollo y despliegue del proyecto BAPE (Bot Administrativo y de Planeación Empresarial), dando cumplimiento a los requerimientos de la fase de desarrollo e integración de módulos.

### 🔗 Repositorio y Control de Versiones (Git)
El proyecto cuenta con control de versiones activo en GitHub. El historial de commits refleja la integración incremental y codificación de los módulos componentes.
*   **Repositorio BAPE**: `https://github.com/IngenieroYlder/000-Backend-FastApi-BAPE1`
*   **Rama principal**: `master`

---

## 1. Tecnologías y Frameworks Utilizados

El proyecto BAPE se construyó utilizando una arquitectura moderna orientada a microservicios, combinando Python para la lógica de negocio profunda y la IA, y Node.js para el manejo en tiempo real de WhatsApp.

### 🐍 Backend Principal (API)
*   **FastAPI**: Framework web principal, utilizado por su extrema rapidez y soporte nativo asíncrono.
*   **Uvicorn**: Servidor web ASGI para levantar la aplicación FastAPI.
*   **Jinja2**: Motor de plantillas (Template Engine) utilizado para renderizar las vistas dinámicas HTML del panel (Dashboard).
*   **APScheduler**: Utilizado de manera interna para programar y ejecutar tareas asíncronas en segundo plano (e.g., comprobación de citas de Google Calendar y envío de recordatorios automáticos).

### 🗄️ Base de Datos y ORM
*   **PostgreSQL 15**: Base de datos relacional principal, elegida por su solidez y capacidad de escalabilidad.
*   **pgvector**: Extensión de PostgreSQL que permite almacenar bases de datos vectoriales. Fundamental para almacenar los *embeddings* de los documentos de conocimiento del cliente, permitiendo que la IA busque respuestas precisas (RAG).
*   **SQLModel**: Orquestador ORM que combina SQLAlchemy y Pydantic, permitiendo declarar la estructura de las tablas y validar los datos que entran por la API simultáneamente.
*   **Alembic**: Herramienta de migraciones de base de datos para controlar el versionamiento de las tablas.

### 🧠 Inteligencia Artificial y Lógica Integrada
*   **OpenAI, Groq, y Google Gemini API**: Proveedores de Modelos de Lenguaje Grandes (LLMs). El sistema está programado para comunicarse dinámicamente con cualquiera de estos tres, basándose en la configuración de la empresa en el panel de `Settings`.
*   **FastEmbed**: Librería de Python para generar *embeddings* vectoriales de texto localmente de forma rápida sin costo en API externas.
*   **Google Calendar API**: Utilizada para la sincronización bidireccional y programación automática de citas gestionadas por la IA o los agentes.

### 🔐 Seguridad y Autenticación
*   **python-jose y passlib (bcrypt)**: Gestión de encriptación de contraseñas y emisión de tokens de seguridad JWT (JSON Web Tokens) para las sesiones de usuario.

### 📱 Motor de WhatsApp
*   **Node.js (v20)**: Entorno de ejecución seleccionado para el microservicio de WhatsApp debido a su superioridad en manejar websockets e hilos concurrentes.
*   **Baileys**: Librería estrella de Node.js que simula el protocolo de WhatsApp Web, permitiendo conectar números mediante código QR sin utilizar la API oficial paga de Meta.
*   **Express**: Framework ligero en Node.js que expone los endpoints internos para que FastAPI le envíe los mensajes generados por la Inteligencia Artificial.

### 🚀 Configuración de Ambientes y DevOps
Para la materialización técnica de la integración de módulos, el ambiente de producción fue configurado de la siguiente manera:
*   **Servidor Host (Hardware)**: VPS (Virtual Private Server) proporcionado por Hostinger, ofreciendo ambiente Linux dedicado.
*   **Gestor de Contenedores**: Docker y Docker Compose para asegurar paridad entre el entorno de desarrollo y producción.
*   **Plataforma de Despliegue (PaaS)**: Dokploy. Configurado para reaccionar vía Webhook al repositorio de GitHub, ejecutando un Pipeline CI/CD que reconstruye la imagen y reinicia los contenedores automáticamente con Zero-Downtime.
*   **Variables de Entorno (.env)**: La inyección de secretos (`POSTGRES_USER`, claves API de OpenAI/Groq, etc) se realiza de forma segura mediante los settings de Dokploy directo al contenedor, sin exponerlos en el código fuente.

---

## 2. Diagramas de Arquitectura

### 📦 Diagrama de Paquetes
Este diagrama expone de forma simplificada cómo está estructurado físicamente el repositorio y las responsabilidades de las carpetas internas en FastAPI.

```mermaid
flowchart TD
    subgraph Repositorio[Proyecto BAPE - Root]
        direction TB
        
        subgraph App[Paquete Core: /app]
            direction LR
            R[routers/] --> S[services/]
            S --> M[models.py / schemas.py]
            Auth[auth.py] --> M
            DB[database.py] --> M
            R --> Auth
            
            subgraph Views[Capa Visual]
                T[templates/]
                St[static/]
            end
            R -.->|Renderiza| Views
        end
        
        subgraph Engine[Paquete Auxiliar: /baileys_engine]
            Node(server.js)
            Lib1(Implementación Baileys)
        end
        
        subgraph Infra[Infraestructura]
            Docker(docker-compose.yml)
            Req(requirements.txt)
            Alembic(alembic/)
            Env(.env)
        end
        
        Infra -.-> App
        Infra -.-> Engine
    end
```

### 🧩 Diagrama de Componentes
Este diagrama ilustra las piezas lógicas del servidor y el ciclo de vida o conexión entre ellas al procesar dinámicas del negocio.

```mermaid
flowchart TB
    %% Definir colores lógicos
    classDef client fill:#f9f,stroke:#333,stroke-width:2px;
    classDef frontend fill:#bbf,stroke:#333,stroke-width:2px;
    classDef backend fill:#dfd,stroke:#333,stroke-width:2px;
    classDef database fill:#fdd,stroke:#333,stroke-width:2px;
    classDef external fill:#ffd,stroke:#333,stroke-width:2px;

    %% Usuarios Finales
    UserClient[Cliente en WhatsApp]:::client
    SaaSAdmin[Dueño o Agente SaaS]:::client

    %% Frontera Externa / Red
    subgraph VPS[Entorno de Despliegue - VPS Dokploy]

        %% Capa de Presentación Dashboard
        subgraph Panel [Frontend HTML/JS BAPE]
            Dashboard[Módulos UI Dashboard]:::frontend
            AuthUI[Interfaz Login]:::frontend
        end

        %% Capa de Negocio (Backend)
        subgraph API [FastAPI Service]
            API_Router[Enrutadores REST]:::backend
            Jinja[Motor Jinja2]:::backend
            Service_AI[Orquestador de IA]:::backend
            Service_CRON[Tareas APScheduler]:::backend
        end

        %% Capa WhatsApp
        subgraph MotorWA [Baileys Node Engine]
            WSC[Conexión WebSocket]:::backend
            WebhookEmit[Emisor Webhooks]:::backend
        end

        %% Persistencia
        subgraph DB Layer [PostgreSQL]
            DB[(BD Relacional BAPE)]:::database
            PGV[(Vector Store PGVector)]:::database
        end
    end

    %% Módulos Externos
    LLMs[OpenAI / Groq / Gemini]:::external
    GC[Google Calendar]:::external
    Meta[Meta / WhatsApp Servers]:::external

    %% Flujos de Información
    SaaSAdmin -->|HTTP/REST| Dashboard
    SaaSAdmin --> AuthUI
    Dashboard <-->|Peticiones + Autenticación| API_Router
    API_Router <-->|Render| Jinja
    Jinja --> Dashboard

    UserClient <-->|Envía/Recibe Mensajes| Meta
    Meta <-->|Sincronización MD| WSC
    WSC --> WebhookEmit
    WebhookEmit -->|POST /webhook/message| API_Router

    API_Router --> Service_AI
    API_Router <--> DB
    Service_AI <--> PGV
    Service_AI <--> LLMs
    
    Service_CRON <--> GC
    Service_AI <--> GC
    
    Service_AI -->|POST Respuesta| WSC
```

### 📊 Diagrama de Clases (ORM Database)
El siguiente diagrama detalla la estructura principal orientada a objetos (Entidad-Relación lógica) programada mediante `SQLModel` en el módulo de persistencia de la aplicación. Muestra cómo la información se relaciona, partiendo del enrutamiento Multi-Tenant (Múltiples empresas).

```mermaid
classDiagram
    direction TB
    class Plan {
        +Integer id
        +String name
        +Float price
        +Boolean is_active
    }
    class Company {
        +Integer id
        +String name
        +Boolean is_active
        +Integer plan_id
    }
    class User {
        +Integer id
        +String email
        +String password_hash
        +String role
        +Boolean is_active
        +Integer company_id
    }
    class Contact {
        +Integer id
        +String phone
        +String name
        +Integer company_id
    }
    class Message {
        +Integer id
        +String text
        +String sender_type
        +DateTime created_at
        +Integer contact_id
    }
    class Product {
        +Integer id
        +String name
        +Float price
        +Integer stock
        +Integer company_id
    }

    Plan "1" <.. "*" Company : suscribed_to
    Company "1" *-- "*" User : has_employees
    Company "1" *-- "*" Contact : has_clients
    Company "1" *-- "*" Product : catalog_items
    Contact "1" *-- "*" Message : chat_history
```

---

## 3. Mapa de Navegación del Sitio (Sitemap UI)
Toda la interfaz del sistema web para la administración por parte del usuario y sus agentes (Frontend).

```mermaid
mindmap
  root((Panel BAPE))
    Autenticación
      Login publico 
      id_post["[POST] Validacion Credenciales"]
    Dashboard "Inicio"
      Gestión de Productos
        Lista inventario
        Formulario creación
      Gestión de Servicios
      Gestión de Categorías
      Gestión de Usuarios
        Invitar a Agentes
        Gestionar Roles Administrativos
    Bandeja de Entrada "Inbox"
      Revisar Chats Activos
      Pausar IA
      Responder Manualmente a Clientes
    Calendario "Agenda"
      Día / Semana / Mes
      Sincronización Google Calendar
      Administrar Disponibilidad
      Crear evento manual
    Contactos "Directorio"
      Historial CRM de WhatsApp
      Perfil del comprador
      Detalles extraídos por la IA
    Canales "Conexión WhatsApp"
      Panel de Códigos QR
      Estado de red (Online / Offline)
    Ajustes "Settings"
      Reglas del Sistema Prompt
      Límites Financieros
      Personalización de Marca
```

---

## 4. Pruebas Unitarias y de Integración (Testing)
Para evidenciar el correcto funcionamiento e integración de cada módulo desarrollado, se establecieron los siguientes protocolos de prueba:

1. **Pruebas de API REST (Backend)**: Funcionalidad validada exhaustivamente mediante rutinas de pruebas manuales y unitarias sobre el panel de control autogenerado por FastAPI (**Swagger UI**). Se verificaron códigos de estado HTTP (200 OK, 401 Unauthorized, 404 Not Found) para registro de clientes, creación de productos y autenticación JWT.
2. **Pruebas del Motor de IA**: Uso de scripts unitarios aislados (ej. `test_openai_direct.py`) para confirmar la resolución DNS y la integridad de la clave API hacia OpenAI antes de conectarlo al pipeline de la base de datos vectorial (pgvector).
3. **Pruebas de Componente UI**: Verificación de carga DOM e inyección de datos provenientes de los Endpoints mediante funciones `fetchAPI` construidas en JavaScript en el Frontend.
4. **Pruebas E2E (End-to-End) sobre WhatsApp**: Interacción en tiempo real escaneando el código QR generado por el microservicio `baileys_engine` y probando de forma integral enviando mensajes, confirmando respuestas automáticas del bot de IA, y validando la captura del lead en la tabla `contacts` de la base de datos PostgreSQL.

---
*Documento generado para la verificación técnica, código fuente y de despliegue del proyecto BAPE, en cumplimiento de la Evidencia Técnica.*
