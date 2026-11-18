import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash

from app.database import DB
from app.models import User

passwords = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)


def issue_token(user_id: int) -> str:
    return jwt.encode(
        {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(hours=2)},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )


def unauthorized() -> HTTPException:
    return HTTPException(401, "Credenciales inválidas", headers={"WWW-Authenticate": "Bearer"})


def current_user(
    db: DB, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
) -> User:
    if credentials is None:
        raise unauthorized()
    try:
        claims = jwt.decode(
            credentials.credentials, os.environ["JWT_SECRET"], algorithms=["HS256"],
            options={"require": ["sub", "exp"]},
        )
        user_id = int(claims["sub"])
    except (jwt.InvalidTokenError, ValueError):
        raise unauthorized() from None
    if not 1 <= user_id <= 2_147_483_647:
        raise unauthorized()
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized()
    return user


CurrentUser = Annotated[User, Depends(current_user)]
