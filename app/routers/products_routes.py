from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app import models, schemas, auth
from app.database import get_session

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@router.post("/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    # Assign company_id from current_user
    new_product = models.Product(**product.dict(), company_id=current_user.company_id)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.get("/", response_model=List[schemas.Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    # Filter by company_id
    stmt = select(models.Product).where(models.Product.company_id == current_user.company_id).offset(skip).limit(limit)
    return db.exec(stmt).all()

@router.get("/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.Product).where(models.Product.id == product_id).where(models.Product.company_id == current_user.company_id)
    product = db.exec(stmt).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@router.put("/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product_update: schemas.ProductUpdate, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.Product).where(models.Product.id == product_id).where(models.Product.company_id == current_user.company_id)
    product = db.exec(stmt).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    for key, value in product_update.dict(exclude_unset=True).items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.Product).where(models.Product.id == product_id).where(models.Product.company_id == current_user.company_id)
    product = db.exec(stmt).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.delete(product)
    db.commit()
    return None
