import hashlib
import jwt
from fastapi import HTTPException, status, Depends
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from .config import settings
from app.db.database import get_async_session, AsyncSession
from app.db.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login/")

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
EXP_TIME = timedelta(minutes=15)


def hashed_password(password):
    hashed = hashlib.md5((password + settings.SALT).encode())
    return hashed.hexdigest()


def create_jwt_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def get_jwt_token(username):
    try:
        return {"access_token": create_jwt_token({
            "sub": username,
            "exp": datetime.utcnow() + EXP_TIME})}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_from_token(token=Depends(oauth2_scheme)) -> str:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM,])
    return payload.get("sub")


async def get_user(current_user, session):
    from_db = await session.execute(select(User).where(User.username == current_user))
    return from_db.scalars().all()[0]
