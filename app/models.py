from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, func, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    # Nuevos campos de perfil
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    products = relationship("Product", back_populates="category_rel")

class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    services = relationship("Service", back_populates="category_rel")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    
    # Nuevos campos
    image = Column(String, nullable=True)
    
    category_id = Column(Integer, ForeignKey("product_categories.id"))
    category_rel = relationship("ProductCategory", back_populates="products")
    
    short_description = Column(String, nullable=True)
    long_description = Column(Text, nullable=True)
    gallery_images = Column(JSON, nullable=True) # Lista de cadenas (URLs) 
    
    description = Column(String, nullable=True)
    price = Column(Numeric, nullable=False)
    stock = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    
    # Nuevos campos
    image = Column(String, nullable=True)
    
    category_id = Column(Integer, ForeignKey("service_categories.id"))
    category_rel = relationship("ServiceCategory", back_populates="services")

    short_description = Column(String, nullable=True)
    long_description = Column(Text, nullable=True)
    gallery_images = Column(JSON, nullable=True) # Lista de cadenas (URLs)

    description = Column(String, nullable=True)
    price = Column(Numeric, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
