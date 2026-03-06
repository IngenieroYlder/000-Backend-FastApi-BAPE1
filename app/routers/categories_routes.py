from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app import models, schemas, auth
from app.database import get_session

router = APIRouter(
    tags=["Categories"]
)

# Categorías de Productos
@router.post("/product-categories", response_model=schemas.Category)
def create_product_category(category: schemas.CategoryCreate, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.ProductCategory).where(models.ProductCategory.name == category.name).where(models.ProductCategory.company_id == current_user.company_id)
    db_cat = db.exec(stmt).first()
    if db_cat:
        raise HTTPException(status_code=400, detail="La categoría ya existe para esta empresa")
    
    new_category = models.ProductCategory(**category.dict(), company_id=current_user.company_id)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.get("/product-categories", response_model=List[schemas.Category])
def read_product_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.ProductCategory).where(models.ProductCategory.company_id == current_user.company_id).offset(skip).limit(limit)
    return db.exec(stmt).all()

@router.delete("/product-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_category(category_id: int, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.ProductCategory).where(models.ProductCategory.id == category_id).where(models.ProductCategory.company_id == current_user.company_id)
    category = db.exec(stmt).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    db.delete(category)
    db.commit()
    return None

# Categorías de Servicios
@router.post("/service-categories", response_model=schemas.Category)
def create_service_category(category: schemas.CategoryCreate, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.ServiceCategory).where(models.ServiceCategory.name == category.name).where(models.ServiceCategory.company_id == current_user.company_id)
    db_cat = db.exec(stmt).first()
    if db_cat:
        raise HTTPException(status_code=400, detail="La categoría ya existe para esta empresa")
    
    new_category = models.ServiceCategory(**category.dict(), company_id=current_user.company_id)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.get("/service-categories", response_model=List[schemas.Category])
def read_service_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.ServiceCategory).where(models.ServiceCategory.company_id == current_user.company_id).offset(skip).limit(limit)
    return db.exec(stmt).all()

@router.delete("/service-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_category(category_id: int, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.ServiceCategory).where(models.ServiceCategory.id == category_id).where(models.ServiceCategory.company_id == current_user.company_id)
    category = db.exec(stmt).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    db.delete(category)
    db.commit()
    return None
