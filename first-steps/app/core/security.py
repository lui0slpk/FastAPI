
import os
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

SECRET_KEY = os.getenv("SECRET_KEY", "change-my-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES", "30"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(
        tz=timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES))
    to_encode.update({"exp": expire})
    token = jwt.encode(payload=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)

    return token


def decode_token(token: str) -> dict:
    playload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])

    return playload


def get_current_user(token: str = Depends(oauth2_scheme)):

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
        headers={"WWW-authenticate": "Bearer"}
    )

    try:
        playload = decode_token(token)
        sub: str | None = playload.get("sub")
        username = str | None = playload.get("username")
        if not sub or username:
            raise credentials_exc

        return {
            "email": sub,
            "username": username
        }
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-authenticate": "Bearer"}
        )
    except InvalidTokenError:
        raise credentials_exc
