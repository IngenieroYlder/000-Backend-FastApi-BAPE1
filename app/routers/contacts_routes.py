from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, col
from app import models, auth
from app.database import get_session
import logging

router = APIRouter(
    prefix="/api/contacts",
    tags=["CRM & Contacts"]
)

logger = logging.getLogger(__name__)

@router.post("/", response_model=models.Contact)
def create_contact(
    phone: str,
    name: Optional[str] = None,
    platform: models.Platform = models.Platform.WHATSAPP,
    is_excluded: bool = False,
    email: Optional[str] = None,
    address: Optional[str] = None,
    birthday: Optional[str] = None,
    company_name: Optional[str] = None,
    job_title: Optional[str] = None,
    document_id: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Create a contact manually in the CRM"""
    # Check if already exists
    stmt = select(models.Contact).where(
        models.Contact.company_id == current_user.company_id,
        models.Contact.phone == phone
    )
    existing = db.exec(stmt).first()
    if existing:
        raise HTTPException(status_code=400, detail="El contacto ya existe")
    
    new_contact = models.Contact(
        company_id=current_user.company_id,
        phone=phone,
        name=name,
        platform=platform,
        is_excluded=is_excluded,
        email=email,
        address=address,
        birthday=birthday,
        company_name=company_name,
        job_title=job_title,
        document_id=document_id
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact

@router.get("/", response_model=List[models.Contact])
def get_contacts(
    db: Session = Depends(get_session), 
    current_user: models.User = Depends(auth.get_current_user),
    search: Optional[str] = None,
    platform: Optional[str] = None
):
    """List all contacts for the company with search and filters"""
    stmt = select(models.Contact).where(models.Contact.company_id == current_user.company_id)
    
    if search:
        stmt = stmt.where(
            (col(models.Contact.name).ilike(f"%{search}%")) | 
            (col(models.Contact.phone).ilike(f"%{search}%"))
        )
    
    if platform:
        stmt = stmt.where(models.Contact.platform == platform)
        
    stmt = stmt.order_by(models.Contact.last_chat_date.desc())
    return db.exec(stmt).all()

@router.get("/{contact_id}", response_model=models.Contact)
def get_contact(
    contact_id: int, 
    db: Session = Depends(get_session), 
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get single contact details"""
    contact = db.get(models.Contact, contact_id)
    if not contact or contact.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return contact

@router.put("/{contact_id}")
def update_contact(
    contact_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    is_excluded: Optional[bool] = None,
    tags: Optional[List[str]] = None,
    internal_notes: Optional[str] = None,
    address: Optional[str] = None,
    birthday: Optional[str] = None,
    company_name: Optional[str] = None,
    job_title: Optional[str] = None,
    document_id: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Update contact CRM data (tags, notes, exclusion)"""
    contact = db.get(models.Contact, contact_id)
    if not contact or contact.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    
    if name is not None: contact.name = name
    if email is not None: contact.email = email
    if is_excluded is not None: contact.is_excluded = is_excluded
    if tags is not None: contact.tags = tags
    if internal_notes is not None: contact.internal_notes = internal_notes
    
    # New Fields
    if address is not None: contact.address = address
    if birthday is not None: contact.birthday = birthday
    if company_name is not None: contact.company_name = company_name
    if job_title is not None: contact.job_title = job_title
    if document_id is not None: contact.document_id = document_id
    
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact

@router.delete("/{contact_id}")
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_session),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Delete a contact and their messages"""
    contact = db.get(models.Contact, contact_id)
    if not contact or contact.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    
    # Messages will be deleted if cascade is set, but SQLModel Relationship handles it if configured.
    # We manually delete just in case or if no cascade.
    stmt_msgs = select(models.Message).where(models.Message.contact_id == contact_id)
    msgs = db.exec(stmt_msgs).all()
    for m in msgs:
        db.delete(m)
        
    db.delete(contact)
    db.commit()
    return {"status": "deleted"}
