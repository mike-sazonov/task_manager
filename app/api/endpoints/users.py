from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.db.database import get_async_session
from app.api.schemas.user import UserCreate
from app.db.models import User
from app.core.security import hashed_password, get_jwt_token_by_name


user_router = APIRouter(
    prefix="/user"
)


@user_router.post("/registrate")
async def reg_user(user: UserCreate, session: AsyncSession = Depends(get_async_session)):
    new_user = User(username=user.username, password=hashed_password(user.password))
    session.add(new_user)
    await session.commit()
    return {"message": f"Пользователь {user.username} успешно зарегистрирован"}


@user_router.post("/login")
async def login_user(user: Annotated[OAuth2PasswordRequestForm, Depends()],
                     session: AsyncSession = Depends(get_async_session)):
    from_db = await session.execute(select(User).where(User.username == user.username))
    current_user = from_db.scalars().all()
    if current_user and current_user[0].password == hashed_password(user.password):
        token = get_jwt_token_by_name(user.username)
        return token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"}
    )

