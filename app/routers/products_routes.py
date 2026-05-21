from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlmodel import Session, select
from app import models, schemas, auth
from app.database import get_session
from app.services.image_service import save_upload, delete_local_image

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

    delete_local_image(product.image)
    for url in product.gallery_images or []:
        delete_local_image(url)
    db.delete(product)
    db.commit()
    return None


def _get_owned_product(db: Session, product_id: int, company_id: int) -> models.Product:
    stmt = (
        select(models.Product)
        .where(models.Product.id == product_id)
        .where(models.Product.company_id == company_id)
    )
    product = db.exec(stmt).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


@router.post("/{product_id}/upload-image", response_model=schemas.Product)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
):
    product = _get_owned_product(db, product_id, current_user.company_id)
    new_url, _thumb = await save_upload(file, "products", current_user.company_id)
    delete_local_image(product.image)
    product.image = new_url
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.post("/{product_id}/upload-gallery", response_model=schemas.Product)
async def upload_product_gallery(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
):
    product = _get_owned_product(db, product_id, current_user.company_id)
    new_url, _thumb = await save_upload(file, "products", current_user.company_id)
    gallery = list(product.gallery_images or [])
    gallery.append(new_url)
    product.gallery_images = gallery
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}/gallery", response_model=schemas.Product)
def delete_product_gallery_image(
    product_id: int,
    url: str,
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
):
    product = _get_owned_product(db, product_id, current_user.company_id)
    gallery = [u for u in (product.gallery_images or []) if u != url]
    product.gallery_images = gallery
    delete_local_image(url)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product
