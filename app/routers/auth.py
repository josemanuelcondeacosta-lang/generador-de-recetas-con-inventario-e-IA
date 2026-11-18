from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import DB
from app.models import User
from app.schemas import Credentials, Token
from app.security import issue_token, passwords, unauthorized

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])
dummy_hash = passwords.hash("contraseña de comparación")


@router.post("/register", response_model=Token, status_code=201)
def register(data: Credentials, db: DB):
    user = User(email=data.email.lower(), password_hash=passwords.hash(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "El correo ya está registrado") from None
    return Token(access_token=issue_token(user.id))


@router.post("/login", response_model=Token)
def login(data: Credentials, db: DB):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    verified = passwords.verify(data.password, user.password_hash if user else dummy_hash)
    if user is None or not verified:
        raise unauthorized()
    return Token(access_token=issue_token(user.id))
