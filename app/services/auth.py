from sqlalchemy.orm import Session
from app.models.auth import User
from app.core.security import verify_password, create_access_token
from fastapi import HTTPException, status
from datetime import timedelta
from app.core.config import settings

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return False
    return user

def login(db: Session, username: str, password: str, remember_me: bool = False):
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Tentukan masa berlaku token berdasarkan role
    if user.role == "superadmin":
        # Superadmin: token berlaku 10 tahun
        expires_delta = timedelta(days=3650)
    elif user.role in ["admin", "boss"] and remember_me:
        # Admin/Boss dengan remember me: 30 hari
        expires_delta = timedelta(days=30)
    else:
        # Lainnya: default dari settings (30 menit)
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(data={"sub": user.username}, expires_delta=expires_delta)
    return {"access_token": access_token, "token_type": "bearer"}