from fastapi import APIRouter


task_router = APIRouter(
    prefix="/task"
)


@task_router.get("/")
async def get_tasks():
    pass


@task_router.post("/")
async def create_task():
    pass


@task_router.put("/")
async def update_task():
    pass


@task_router.delete("/")
async def delete_task():
    pass


