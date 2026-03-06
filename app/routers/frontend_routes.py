from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    tags=["Frontend"]
)

templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/inbox", response_class=HTMLResponse)
async def get_inbox_page(request: Request):
    return templates.TemplateResponse("inbox.html", {"request": request})

@router.get("/settings", response_class=HTMLResponse)
async def get_settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

@router.get("/channels", response_class=HTMLResponse)
async def get_channels_page(request: Request):
    return templates.TemplateResponse("channels.html", {"request": request})

@router.get("/", response_class=HTMLResponse)
async def root_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
@router.get("/contacts", response_class=HTMLResponse)
async def get_contacts_page(request: Request):
    return templates.TemplateResponse("contacts.html", {"request": request})

@router.get("/calendar", response_class=HTMLResponse)
async def get_calendar_page(request: Request):
    return templates.TemplateResponse("calendar.html", {"request": request})
