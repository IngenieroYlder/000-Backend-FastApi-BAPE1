from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import auth_routes as auth, frontend_routes, whatsapp_routes, webhooks, chat_routes, settings_routes
from app.database import engine
from fastapi.templating import Jinja2Templates

app = FastAPI(title="BAPE Backend")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

import os
media_dir = os.path.join(os.path.dirname(__file__), "..", "baileys_engine", "media")
os.makedirs(media_dir, exist_ok=True)
app.mount("/media", StaticFiles(directory=media_dir), name="media")

# Setup Templates
templates = Jinja2Templates(directory="app/templates")

# Routers (Rutas)
from app.routers import (
    auth_routes as auth,
    frontend_routes,
    whatsapp_routes,
    webhooks,
    chat_routes,
    settings_routes,
    products_routes,
    services_routes,
    users_routes,
    categories_routes,
    calendar_routes,
    contacts_routes
)

app.include_router(auth.router)
app.include_router(frontend_routes.router)
app.include_router(whatsapp_routes.router)
app.include_router(webhooks.router)
app.include_router(chat_routes.router)
app.include_router(settings_routes.router)
app.include_router(products_routes.router)
app.include_router(services_routes.router)
app.include_router(users_routes.router)
app.include_router(categories_routes.router)
app.include_router(calendar_routes.router)
app.include_router(contacts_routes.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    """
    Restore WhatsApp sessions on backend startup.
    """
    import asyncio
    import httpx
    import json
    import os
    import logging
    from app.services.qr_cache import qr_cache

    logger = logging.getLogger(__name__)

    # Emergency Fallback Pre-population
    if os.path.exists("emergency_sessions.json"):
        try:
            with open("emergency_sessions.json", "r") as f:
                emergency_data = json.load(f)
                for s in emergency_data:
                    qr_cache.update_metadata(s["session_name"], s)
            logger.info("Emergency sessions loaded into cache.")
            print("[Startup] Emergency sessions loaded into cache.")
        except Exception as e:
            logger.error(f"Error loading emergency sessions: {e}")

    session_restore_task = asyncio.create_task(restore_sessions())
    
    # Start Scheduler
    from app.services.scheduler_service import scheduler_service
    scheduler_service.start()

async def restore_sessions():
    import asyncio
    import os
    import httpx
    from sqlmodel import select, Session
    from app.models import WhatsAppSession
    from app.database import engine
    from app.config import BAILEYS_ENGINE_URL
    import logging

    logger = logging.getLogger(__name__)

    await asyncio.sleep(5) # Give Baileys 5s to boot
    
    try:
        # Use a localized session and a timeout for the DB query
        from concurrent.futures import ThreadPoolExecutor
        loop = asyncio.get_event_loop()
        
        def _get_items():
            with Session(engine) as db_session:
                params_stmt = select(WhatsAppSession)
                return db_session.exec(params_stmt).all()
        
        wa_sessions = await asyncio.wait_for(loop.run_in_executor(None, _get_items), timeout=5.0)
        
        logger.info(f"Restoring {len(wa_sessions)} WhatsApp sessions...")
        print(f"[Startup] Found {len(wa_sessions)} sessions to restore.")
        
        base_url = os.getenv("BASE_PUBLIC_URL", "http://127.0.0.1:8003")
        webhook_url = f"{base_url.rstrip('/')}/webhook" 
        
        async with httpx.AsyncClient() as client:
            for wa_session in wa_sessions:
                try:
                    payload = {
                        "session_name": wa_session.session_name,
                        "webhook_url": webhook_url
                    }
                    resp = await client.post(f"{BAILEYS_ENGINE_URL}/session/init", json=payload)
                    if resp.status_code == 200:
                        print(f"[Startup] Session {wa_session.session_name} restored.")
                except Exception as e:
                    print(f"[Startup] Error restoring {wa_session.session_name}: {e}")
    except asyncio.TimeoutError:
        print("[Startup] Database timeout during session restoration. Skipping DB initialization, relying on cache/webhooks.")
    except Exception as e:
        print(f"[Startup] Unexpected error during session restoration: {e}")
