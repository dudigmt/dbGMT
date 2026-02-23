from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.schemas.auth import Token
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(
    username: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    - remember_me: jika true dan user adalah admin/boss, token berlaku 30 hari.
    - superadmin selalu mendapat token 10 tahun.
    - user biasa mendapat token 30 menit.
    """
    return auth_service.login(db, username, password, remember_me)