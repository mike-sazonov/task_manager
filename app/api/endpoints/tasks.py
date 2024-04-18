from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from typing import Annotated
from sqlalchemy import select, update, delete, insert

from app.db.models import Task
from app.db.database import AsyncSession, get_async_session
from app.api.schemas.task import NewTask
from app.core.security import get_user_from_token

task_router = APIRouter(
    prefix="/task"
)

connected_clients = []


async def get_task_list(client, session: AsyncSession = Depends(get_async_session)):
    from_db = await session.execute(select(Task).order_by(-Task.id))
    task_list = from_db.scalars().all()
    for task in task_list:
        await client.send_text(
            f"Задача №{task.id}, {task.text}, статус: {('Не выполнена', 'Выполнена')[task.complete]}"
        )


@task_router.get("/")
async def get_tasks(
        task_id: int,
        current_user: Annotated[str, Depends(get_user_from_token)],
        session: AsyncSession = Depends(get_async_session)):

    current_task = await session.execute(select(Task).filter(Task.id == task_id))
    task = current_task.scalars().all()[0]
    return NewTask(text=task.text, complete=task.complete)


@task_router.post("/")
async def create_task(
        task: NewTask,
        current_user: Annotated[str, Depends(get_user_from_token)],
        session: AsyncSession = Depends(get_async_session)):

    await session.execute(insert(Task), task.model_dump())
    await session.commit()
    for client in connected_clients:
        await client.send_text(f"Пользователь {current_user} добавил задачу: {task.text}")
        await get_task_list(client, session)


@task_router.put("/")
async def update_task(
        task_id: int,
        task: NewTask,
        current_user: Annotated[str, Depends(get_user_from_token)],
        session: AsyncSession = Depends(get_async_session),
        ):
    print(task)
    await session.execute(update(Task).values(task.model_dump()).where(Task.id == task_id))
    await session.commit()
    for client in connected_clients:
        await client.send_text(f"Пользователь {current_user} обновил задачу № {task_id}")
        await get_task_list(client, session)


@task_router.delete("/")
async def delete_task(
        task_id: int,
        current_user: Annotated[str, Depends(get_user_from_token)],
        session: AsyncSession = Depends(get_async_session)):

    await session.execute(delete(Task).where(Task.id == task_id))
    await session.commit()
    for client in connected_clients:
        await client.send_text(f"Пользователь {current_user} удалил задачу № {task_id}")
        await get_task_list(client, session)


@task_router.websocket("/task_board/")
async def websocket_endpoint(
        websocket: WebSocket,
        session: AsyncSession = Depends(get_async_session)):

    await websocket.accept()
    await websocket.send_text("Введите ваш JWT-токен")
    token = await websocket.receive_text()
    user = get_user_from_token(token)
    if user is None:
        await websocket.close(code=1008)
        return
    connected_clients.append(websocket)
    await get_task_list(websocket, session)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
