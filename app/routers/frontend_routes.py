from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    tags=["Frontend"]
)

templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")

@router.get("/inbox", response_class=HTMLResponse)
async def get_inbox_page(request: Request):
    return templates.TemplateResponse(request, "inbox.html")

@router.get("/settings", response_class=HTMLResponse)
async def get_settings_page(request: Request):
    return templates.TemplateResponse(request, "settings.html")

@router.get("/channels", response_class=HTMLResponse)
async def get_channels_page(request: Request):
    return templates.TemplateResponse(request, "channels.html")

@router.get("/", response_class=HTMLResponse)
async def root_page(request: Request):
    return templates.TemplateResponse(request, "login.html")
@router.get("/contacts", response_class=HTMLResponse)
async def get_contacts_page(request: Request):
    return templates.TemplateResponse(request, "contacts.html")

@router.get("/calendar", response_class=HTMLResponse)
async def get_calendar_page(request: Request):
    return templates.TemplateResponse(request, "calendar.html")
