from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, auth
from app.database import get_db

router = APIRouter(
    tags=["Categories"]
)

# Categorías de Productos
@router.post("/product-categories", response_model=schemas.Category)
def create_product_category(category: schemas.CategoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_cat = db.query(models.ProductCategory).filter(models.ProductCategory.name == category.name).first()
    if db_cat:
        raise HTTPException(status_code=400, detail="Category already exists")
    new_category = models.ProductCategory(**category.dict())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.get("/product-categories", response_model=List[schemas.Category])
def read_product_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.ProductCategory).offset(skip).limit(limit).all()

@router.delete("/product-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_category(category_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    category = db.query(models.ProductCategory).filter(models.ProductCategory.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return None

# Categorías de Servicios
@router.post("/service-categories", response_model=schemas.Category)
def create_service_category(category: schemas.CategoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_cat = db.query(models.ServiceCategory).filter(models.ServiceCategory.name == category.name).first()
    if db_cat:
        raise HTTPException(status_code=400, detail="Category already exists")
    new_category = models.ServiceCategory(**category.dict())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.get("/service-categories", response_model=List[schemas.Category])
def read_service_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.ServiceCategory).offset(skip).limit(limit).all()

@router.delete("/service-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_category(category_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    category = db.query(models.ServiceCategory).filter(models.ServiceCategory.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return None
