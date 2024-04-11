from fastapi import APIRouter


user_router = APIRouter(
    prefix="/user"
)


@user_router.post("/registrate")
async def reg_user():
    pass


@user_router.post("/login")
async def login_user():
    pass
