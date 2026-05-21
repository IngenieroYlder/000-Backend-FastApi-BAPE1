from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlmodel import Session, select
from app import models, schemas, auth
from app.database import get_session
from app.services.image_service import save_upload, delete_local_image

router = APIRouter(
    prefix="/services",
    tags=["Services"]
)

@router.post("/", response_model=schemas.Service)
def create_service(service: schemas.ServiceCreate, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    new_service = models.Service(**service.dict(), company_id=current_user.company_id)
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    return new_service

@router.get("/", response_model=List[schemas.Service])
def read_services(skip: int = 0, limit: int = 100, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.Service).where(models.Service.company_id == current_user.company_id).offset(skip).limit(limit)
    return db.exec(stmt).all()

@router.get("/{service_id}", response_model=schemas.Service)
def read_service(service_id: int, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.Service).where(models.Service.id == service_id).where(models.Service.company_id == current_user.company_id)
    service = db.exec(stmt).first()
    if service is None:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return service

@router.put("/{service_id}", response_model=schemas.Service)
def update_service(service_id: int, service_update: schemas.ServiceUpdate, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.Service).where(models.Service.id == service_id).where(models.Service.company_id == current_user.company_id)
    service = db.exec(stmt).first()
    if service is None:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    
    for key, value in service_update.dict(exclude_unset=True).items():
        setattr(service, key, value)
    
    db.commit()
    db.refresh(service)
    return service

@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: int, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.Service).where(models.Service.id == service_id).where(models.Service.company_id == current_user.company_id)
    service = db.exec(stmt).first()
    if service is None:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    delete_local_image(service.image)
    for url in service.gallery_images or []:
        delete_local_image(url)
    db.delete(service)
    db.commit()
    return None


def _get_owned_service(db: Session, service_id: int, company_id: int) -> models.Service:
    stmt = (
        select(models.Service)
        .where(models.Service.id == service_id)
        .where(models.Service.company_id == company_id)
    )
    service = db.exec(stmt).first()
    if service is None:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return service


@router.post("/{service_id}/upload-image", response_model=schemas.Service)
async def upload_service_image(
    service_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
):
    service = _get_owned_service(db, service_id, current_user.company_id)
    new_url, _thumb = await save_upload(file, "services", current_user.company_id)
    delete_local_image(service.image)
    service.image = new_url
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.post("/{service_id}/upload-gallery", response_model=schemas.Service)
async def upload_service_gallery(
    service_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
):
    service = _get_owned_service(db, service_id, current_user.company_id)
    new_url, _thumb = await save_upload(file, "services", current_user.company_id)
    gallery = list(service.gallery_images or [])
    gallery.append(new_url)
    service.gallery_images = gallery
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.delete("/{service_id}/gallery", response_model=schemas.Service)
def delete_service_gallery_image(
    service_id: int,
    url: str,
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user),
):
    service = _get_owned_service(db, service_id, current_user.company_id)
    gallery = [u for u in (service.gallery_images or []) if u != url]
    service.gallery_images = gallery
    delete_local_image(url)
    db.add(service)
    db.commit()
    db.refresh(service)
    return service
