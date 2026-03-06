from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Dict
from datetime import datetime

# Esquemas de Tokens
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Esquemas de Usuario
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserRegister(UserCreate):
    company_name: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    role: str
    company_id: Optional[int] = None

    class Config:
        from_attributes = True

# Esquemas de Categoría
class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Reutilizando estructura de esquema de Categoría ya que coinciden, pero con diferencia lógica en endpoints
ProductCategory = Category
ServiceCategory = Category

# Campos Comunes
class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image: Optional[str] = None
    category_id: Optional[int] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    gallery_images: Optional[List[str]] = []

# Esquemas de Producto
class ProductBase(ItemBase):
    stock: int

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    image: Optional[str] = None
    category_id: Optional[int] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    gallery_images: Optional[List[str]] = None

class Product(ProductBase):
    id: int
    created_at: datetime
    category_rel: Optional[ProductCategory] = None

    class Config:
        from_attributes = True

# Esquemas de Servicio
class ServiceBase(ItemBase):
    pass

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image: Optional[str] = None
    category_id: Optional[int] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    gallery_images: Optional[List[str]] = None

class Service(ServiceBase):
    id: int
    created_at: datetime
    category_rel: Optional[ServiceCategory] = None

class CompanySettingsUpdate(BaseModel):
    system_prompt: Optional[str] = None
    golden_rules: Optional[str] = None
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    telegram_token: Optional[str] = None
    verify_token: Optional[str] = None
    facebook_page_id: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    whitelisted_ips: Optional[Dict[str, Any]] = None
    session_timeout_hours: Optional[int] = None
