from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app import models, schemas, auth
from app.database import get_session
from app.config import settings
from app.models import UserRole

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register", response_model=schemas.User)
def register_user(user_data: schemas.UserRegister, db: Session = Depends(get_session)):
    # 1. Check if user exists
    stmt = select(models.User).where(models.User.email == user_data.email)
    db_user = db.exec(stmt).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")

    # 2. Create Company
    # Check if company name exists (optional strictness)
    stmt_comp = select(models.Company).where(models.Company.name == user_data.company_name)
    if db.exec(stmt_comp).first():
         raise HTTPException(status_code=400, detail="El nombre de la empresa ya está registrado")

    # Get Default Plan (Free) or create if not exists (handled by seed, but good to have fallback)
    stmt_plan = select(models.Plan).where(models.Plan.name == "Free")
    plan = db.exec(stmt_plan).first()
    if not plan:
         # Fallback or error
         raise HTTPException(status_code=500, detail="Plan por defecto no encontrado")

    new_company = models.Company(
        name=user_data.company_name,
        plan_id=plan.id,
        is_active=True
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    
    # 3. Create User
    hashed_password = auth.get_password_hash(user_data.password)
    new_user = models.User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        is_active=True,
        role=UserRole.SUPERADMIN,
        company_id=new_company.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    stmt = select(models.User).where(models.User.email == form_data.username)
    user = db.exec(stmt).first()
    
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role.value, "company_id": user.company_id}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
