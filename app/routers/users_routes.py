from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlmodel import Session, select
from app import models, schemas, auth
from app.database import get_session
from app.models import UserRole

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/", response_model=List[schemas.User])
def get_users(db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    # 1. RBAC: Only Admin/Superadmin
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
         raise HTTPException(status_code=403, detail="No tienes permisos para ver usuarios")

    # 2. SaaS Isolation
    stmt = select(models.User).where(models.User.company_id == current_user.company_id)
    users = db.exec(stmt).all()
    return users

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    # 1. RBAC
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
         raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")

    # Check email global uniqueness (or per company? Usually email is global login)
    stmt = select(models.User).where(models.User.email == user.email)
    if db.exec(stmt).first():
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        is_active=True,
        role=UserRole.AGENT, # Default role for created users? Or pass in schema?
        company_id=current_user.company_id # Force company_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.User).where(models.User.id == user_id)
    db_user = db.exec(stmt).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # SaaS: Check company
    if db_user.company_id != current_user.company_id:
         raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # RBAC: Self or Admin
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]
    if not is_admin and db_user.id != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes editar este usuario")

    # Update logic
    if user_update.email:
        # Check unique
        stmt_exist = select(models.User).where(models.User.email == user_update.email)
        existing_email = db.exec(stmt_exist).first()
        if existing_email and existing_email.id != user_id:
             raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")
        db_user.email = user_update.email
        
    if user_update.first_name is not None:
        db_user.first_name = user_update.first_name
    if user_update.last_name is not None:
        db_user.last_name = user_update.last_name
    if user_update.phone is not None:
        db_user.phone = user_update.phone

    if user_update.password:
        db_user.password_hash = auth.get_password_hash(user_update.password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.User).where(models.User.id == user_id)
    db_user = db.exec(stmt).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # SaaS
    if db_user.company_id != current_user.company_id:
         raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # RBAC
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar usuarios")

    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta")

    db.delete(db_user)
    db.commit()
    return None

@router.put("/{user_id}/status", response_model=schemas.User)
def toggle_user_status(user_id: int, is_active: bool, db: Session = Depends(get_session), current_user: models.User = Depends(auth.get_current_user)):
    stmt = select(models.User).where(models.User.id == user_id)
    db_user = db.exec(stmt).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if db_user.company_id != current_user.company_id:
         raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
         raise HTTPException(status_code=403, detail="No tienes permisos para administrar usuarios")

    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes desactivar tu propia cuenta")

    db_user.is_active = is_active
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
