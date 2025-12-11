from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas, auth
from app.database import get_db

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/", response_model=List[schemas.User])
def get_users(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Optional: Check if current_user is admin
    users = db.query(models.User).all()
    return users

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        password_hash=hashed_password,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Permission check: Users can only update themselves unless they are admin (logic can be expanded later)
    # For now, allow anyone to update anyone? No, that's unsafe. 
    # Let's enforce: Users can only update THEMSELVES.
    if user_id != current_user.id:
        # TODO: Add 'is_admin' check if we want admins to edit others
        raise HTTPException(status_code=403, detail="Not authorized to update this user")

    # Update fields
    if user_update.email:
        # Check uniqueness
        existing_email = db.query(models.User).filter(models.User.email == user_update.email).first()
        if existing_email and existing_email.id != user_id:
             raise HTTPException(status_code=400, detail="Email already registered by another user")
        db_user.email = user_update.email
        
    if user_update.first_name is not None:
        db_user.first_name = user_update.first_name
    if user_update.last_name is not None:
        db_user.last_name = user_update.last_name
    if user_update.phone is not None:
        db_user.phone = user_update.phone
        
    if user_update.password:
        db_user.password_hash = auth.get_password_hash(user_update.password)

    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting oneself
    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    db.delete(db_user)
    db.commit()
    return None

@router.put("/{user_id}/status", response_model=schemas.User)
def toggle_user_status(user_id: int, is_active: bool, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Prevent disabling oneself
    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot disable your own account")

    db_user.is_active = is_active
    db.commit()
    db.refresh(db_user)
    return db_user
