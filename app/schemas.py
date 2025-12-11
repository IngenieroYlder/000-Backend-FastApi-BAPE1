from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime

# Esquemas de Tokens
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Esquemas de Usuario
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime 

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

    class Config:
        from_attributes = True
