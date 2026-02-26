from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, Text, BigInteger

# --- ENUMS ---
class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    AGENT = "agent"

class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Platform(str, Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    INSTAGRAM = "instagram"
    MESSENGER = "messenger"
    WEB = "web"

# --- SAAS CORE ---

class Plan(SQLModel, table=True):
    __tablename__ = "plans"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    price: float = Field(default=0.0)
    limits: Dict = Field(default={}, sa_column=Column(JSON)) # JSON: {"max_users": 5, "max_bots": 1}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    companies: List["Company"] = Relationship(back_populates="plan")

class Company(SQLModel, table=True):
    __tablename__ = "companies"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    plan_id: Optional[int] = Field(default=None, foreign_key="plans.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    plan: Optional[Plan] = Relationship(back_populates="companies")
    campaigns: List["Campaign"] = Relationship(back_populates="company")
    users: List["User"] = Relationship(back_populates="company")
    contacts: List["Contact"] = Relationship(back_populates="company")
    knowledge_docs: List["KnowledgeDocument"] = Relationship(back_populates="company")
    
    # 1-to-1 relationship with AppointmentConfig
    appointment_config: Optional["AppointmentConfig"] = Relationship(back_populates="company", sa_relationship_kwargs={"uselist": False})
    products: List["Product"] = Relationship(back_populates="company")
    services: List["Service"] = Relationship(back_populates="company")
    whatsapp_sessions: List["WhatsAppSession"] = Relationship(back_populates="company")
    settings: Optional["CompanySettings"] = Relationship(back_populates="company")
    appointments: List["Appointment"] = Relationship(back_populates="company")
    logs: List["SystemLog"] = Relationship(back_populates="company")

class CompanySettings(SQLModel, table=True):
    __tablename__ = "company_settings"
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(unique=True, foreign_key="companies.id")
    
    # AI & Prompts
    system_prompt: Optional[str] = Field(default="Eres un asistente útil.", sa_column=Column(Text))
    golden_rules: Optional[str] = Field(default=None, sa_column=Column(Text))
    summary_prompt: Optional[str] = Field(default="Eres un experto en resumir conversaciones de ventas y soporte. Tu objetivo es crear un resumen CONCISO pero rico en contexto. Incluye: Nombres, Intenciones de compra, Datos clave (dirección, teléfono), y Estado actual. NO incluyas saludos genéricos. El resumen debe servir para que el próximo agente entienda todo en 5 segundos.", sa_column=Column(Text))
    image_prompt: Optional[str] = Field(default="El usuario ha enviado esta imagen. Analízala brevemente e intégrala a la conversación si es relevante.", sa_column=Column(Text))
    
    # Branding
    logo_url: Optional[str] = None
    icon_url: Optional[str] = None
    favicon_url: Optional[str] = None
    
    # Integrations (OpenAI)
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    
    # Integrations (Meta/WhatsApp Cloud if used directly later)
    whatsapp_token: Optional[str] = None
    phone_number_id: Optional[str] = None
    
    # Integrations (Meta App)
    verify_token: Optional[str] = None
    facebook_page_id: Optional[str] = None
    instagram_id: Optional[str] = None
    
    # Integrations (Telegram)
    telegram_token: Optional[str] = None
    
    # Integrations (Email / SMTP)
    smtp_host: Optional[str] = None # e.g. smtp.gmail.com
    smtp_port: Optional[int] = None # e.g. 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    
    # Security
    whitelisted_ips: Optional[Dict] = Field(default={}, sa_column=Column(JSON))
    session_timeout_hours: int = Field(default=8)
    
    company: "Company" = Relationship(back_populates="settings")

class Campaign(SQLModel, table=True):
    __tablename__ = "campaigns"
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id")
    name: str
    status: str = Field(default="draft") # draft, active, paused, finished
    type: str = Field(default="broadcast") # broadcast, drip
    config: Dict = Field(default={}, sa_column=Column(JSON)) # Audience filters, schedule
    metrics: Dict = Field(default={}, sa_column=Column(JSON)) # sent, delivered, read, replied
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    company: Optional["Company"] = Relationship(back_populates="campaigns")

class KnowledgeDocument(SQLModel, table=True):
    __tablename__ = "knowledge_documents"
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id")
    
    filename: str
    file_path: str
    status: str = Field(default="processed") # processing, processed, error
    content: Optional[str] = Field(default=None, sa_column=Column(Text)) # Extracted text
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    company: "Company" = Relationship(back_populates="knowledge_docs")
    chunks: List["DocumentChunk"] = Relationship(back_populates="document", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunks"
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="knowledge_documents.id")
    chunk_index: int
    content: str
    embedding: Optional[str] = Field(sa_column=Column(Text)) # Specific JSON string for vector
    
    document: Optional["KnowledgeDocument"] = Relationship(back_populates="chunks")

class AppointmentConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id") # Corrected foreign key to "companies.id"
    
    # Time Configuration
    slot_duration: int = Field(default=30)  # Minutes
    gap_between_slots: int = Field(default=0) # Minutes
    
    # Schedule (JSON): {"mon": ["09:00-12:00", "14:00-18:00"], ...}
    working_hours: Dict = Field(default={}, sa_column=Column(JSON))
    timezone: str = Field(default="America/Bogota")
    
    # Google Credentials
    google_calendar_id: str = Field(default="primary")
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_access_token: Optional[str] = None
    google_refresh_token: Optional[str] = None
    token_expiry: Optional[datetime] = None
    
    # Rules
    mandatory_fields: Dict = Field(default={"name": True, "email": True, "phone": True}, sa_column=Column(JSON))
    
    # Reminders (JSON): [{"hours_before": 24, "id": 1}, {"hours_before": 1, "id": 2}]
    reminder_rules: List = Field(default=[], sa_column=Column(JSON))
    
    company: Optional["Company"] = Relationship(back_populates="appointment_config")

class Appointment(SQLModel, table=True):
    __tablename__ = "appointments"
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id")
    
    title: str
    start_time: datetime
    end_time: datetime
    
    client_name: str
    client_phone: str
    client_email: Optional[str] = None
    
    status: str = Field(default="confirmed") # confirmed, cancelled
    google_event_id: Optional[str] = None
    
    # List of rule IDs that have already been sent
    reminders_sent: List[int] = Field(default=[], sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    company: Optional["Company"] = Relationship(back_populates="appointments")
    
    # Link to CRM Contact
    contact_id: Optional[int] = Field(default=None, foreign_key="contacts.id")
    contact: Optional["Contact"] = Relationship(back_populates="appointments")


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = Field(default=UserRole.AGENT)
    is_active: bool = Field(default=True)
    
    company_id: Optional[int] = Field(default=None, foreign_key="companies.id")
    company: Optional[Company] = Relationship(back_populates="users")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

# --- CATALOG (Business Logic) ---

class ProductCategory(SQLModel, table=True):
    __tablename__ = "product_categories"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    company_id: Optional[int] = Field(default=None, foreign_key="companies.id")
    
    products: List["Product"] = Relationship(back_populates="category")

class Product(SQLModel, table=True):
    __tablename__ = "products"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    price: float = Field(default=0.0)
    stock: int = Field(default=0)
    image: Optional[str] = None
    gallery_images: List[str] = Field(default=[], sa_column=Column(JSON))
    
    category_id: Optional[int] = Field(default=None, foreign_key="product_categories.id")
    category: Optional[ProductCategory] = Relationship(back_populates="products")
    
    company_id: Optional[int] = Field(default=None, foreign_key="companies.id")
    company: Optional[Company] = Relationship(back_populates="products")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ServiceCategory(SQLModel, table=True):
    __tablename__ = "service_categories"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    company_id: Optional[int] = Field(default=None, foreign_key="companies.id")
    
    services: List["Service"] = Relationship(back_populates="category")

class Service(SQLModel, table=True):
    __tablename__ = "services"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    price: float = Field(default=0.0)
    image: Optional[str] = None
    gallery_images: List[str] = Field(default=[], sa_column=Column(JSON))

    category_id: Optional[int] = Field(default=None, foreign_key="service_categories.id")
    category: Optional[ServiceCategory] = Relationship(back_populates="services")
    
    company_id: Optional[int] = Field(default=None, foreign_key="companies.id")
    company: Optional[Company] = Relationship(back_populates="services")

    created_at: datetime = Field(default_factory=datetime.utcnow)

# --- CHAT & COMMUNICATIONS ---

class Contact(SQLModel, table=True):
    __tablename__ = "contacts"
    id: Optional[int] = Field(default=None, primary_key=True)
    phone: str = Field(index=True) # E.164 format
    name: Optional[str] = None
    email: Optional[str] = None
    
    platform: Platform = Field(default=Platform.WHATSAPP)
    is_paused: bool = Field(default=False)
    paused_until: Optional[datetime] = None
    
    # CRM & Bot Control
    is_excluded: bool = Field(default=False)
    tags: List[str] = Field(default=[], sa_column=Column(JSON))
    internal_notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Detailed CRM Fields
    address: Optional[str] = None
    birthday: Optional[str] = None # Or datetime if strictly needed
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    document_id: Optional[str] = None # DNI/Cedula
    
    company_id: Optional[int] = Field(default=None, foreign_key="companies.id")
    
    company: Optional[Company] = Relationship(back_populates="contacts")
    messages: List["Message"] = Relationship(back_populates="contact")
    appointments: List["Appointment"] = Relationship(back_populates="contact")
    
    # Context & Memory
    summary: Optional[str] = Field(default=None, sa_column=Column(Text))
    last_chat_date: datetime = Field(default_factory=datetime.utcnow)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Message(SQLModel, table=True):
    __tablename__ = "messages"
    id: Optional[int] = Field(default=None, primary_key=True)
    contact_id: Optional[int] = Field(default=None, foreign_key="contacts.id")
    session_id: Optional[int] = Field(default=None, foreign_key="whatsapp_sessions.id") # Link to specific instance
    
    role: MessageRole = Field(default=MessageRole.USER)
    content: Optional[str] = Field(default=None, sa_column=Column(Text))
    type: MessageType = Field(default=MessageType.TEXT)
    media_url: Optional[str] = None
    sender_name: Optional[str] = None # Name of sender (agent or contact)
    
    company_id: Optional[int] = Field(default=None, foreign_key="companies.id")
    
    contact: Optional[Contact] = Relationship(back_populates="messages")
    session: Optional["WhatsAppSession"] = Relationship(back_populates="messages")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WhatsAppSession(SQLModel, table=True):
    __tablename__ = "whatsapp_sessions"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_name: str = Field(index=True) # ID unique for Baileys (e.g. company_1_instance_5)
    alias: str = Field(default="Principal") # Human readable name (e.g. "Ventas", "Soporte")
    phone_number: Optional[str] = None # The connected number
    is_active: bool = Field(default=True)
    
    company_id: int = Field(foreign_key="companies.id")
    status: str = Field(default="disconnected") # connected, qr_ready, disconnected
    qr_code: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # AI Configuration
    system_prompt: Optional[str] = Field(default="Eres un asistente útil.", sa_column=Column(Text))
    ai_provider: str = Field(default="openai") # openai, groq, gemini
    ai_strategy: str = Field(default="fixed") # fixed, rotate_free
    
    # Bot Control
    respond_to_groups: bool = Field(default=False)
    is_bot_enabled: bool = Field(default=True)
    
    company: Company = Relationship(back_populates="whatsapp_sessions")
    messages: List[Message] = Relationship(back_populates="session")
    last_active: datetime = Field(default_factory=datetime.utcnow)

class SystemLog(SQLModel, table=True):
    __tablename__ = "system_logs"
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id")
    event_type: str # error, warning, info, rotation
    provider: Optional[str] = None
    message: str = Field(sa_column=Column(Text))
    details: Optional[Dict] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    company: Company = Relationship(back_populates="logs")

