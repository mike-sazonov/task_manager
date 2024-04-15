from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from typing import Annotated
from sqlalchemy import select, update, delete, insert

from app.db.models import Task
from app.db.database import AsyncSession, get_async_session
from app.api.schemas.task import NewTask
from app.core.security import get_user_from_token, get_user_from_db


task_router = APIRouter(
    prefix="/task"
)

connected_clients = []


async def get_task_list(client, session: AsyncSession = Depends(get_async_session)):
    from_db = await session.execute(select(Task).order_by(-Task.id))
    task_list = from_db.scalars().all()
    for task in task_list:
        await client.send_text(f"Задача №{task.id}, {task.text}, статус: {task.complete}")


@task_router.get("/")
async def get_tasks(
        task_id: int,
        current_user: Annotated[str, Depends(get_user_from_token)],
        session: AsyncSession = Depends(get_async_session)):

    if get_user_from_db(current_user):
        current_task = await session.execute(select(Task).filter(Task.id == task_id))
        return current_task.scalars().all()
    else:
        raise HTTPException(status_code=403, detail="Not authorized")


@task_router.post("/")
async def create_task(
        task: NewTask,
        current_user: Annotated[str, Depends(get_user_from_token)],
        session: AsyncSession = Depends(get_async_session)):

    if get_user_from_db(current_user):
        await session.execute(insert(Task), task.model_dump())
        await session.commit()
        for client in connected_clients:
            await client.send_text(f"Пользователь {current_user} добавил задачу: {task.text}")
            await get_task_list(client, session)
    else:
        raise HTTPException(status_code=403, detail="Not authorized")


@task_router.put("/")
async def update_task(
        task_id: int,
        task: NewTask,
        current_user: Annotated[str, Depends(get_user_from_token)],
        session: AsyncSession = Depends(get_async_session)):

    if get_user_from_db(current_user):
        await session.execute(update(Task).values(task.model_dump()).where(Task.id == task_id))
        await session.commit()
        for client in connected_clients:
            await client.send_text(f"Пользователь {current_user} обновил задачу № {task_id}")
            await get_task_list(client, session)
    else:
        raise HTTPException(status_code=403, detail="Not authorized")


@task_router.delete("/")
async def delete_task(
        task_id: int,
        current_user: Annotated[str, Depends(get_user_from_token)],
        session: AsyncSession = Depends(get_async_session)):
    if get_user_from_db(current_user):
        await session.execute(delete(Task).where(Task.id == task_id))
        await session.commit()
        for client in connected_clients:
            await client.send_text(f"Пользователь {current_user} удалил задачу № {task_id}")
            await get_task_list(client, session)
    else:
        raise HTTPException(status_code=403, detail="Not authorized")


@task_router.websocket("/task_board/")
async def websocket_endpoint(
        websocket: WebSocket,
        session: AsyncSession = Depends(get_async_session)):

    await websocket.accept()
    connected_clients.append(websocket)
    await get_task_list(websocket, session)

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(data)
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
