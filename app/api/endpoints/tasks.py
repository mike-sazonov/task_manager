from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from typing import Annotated
from sqlalchemy import select, update, delete, insert, desc

from app.db.models import Task
from app.db.database import AsyncSession, get_async_session
from app.api.schemas.task import NewTask
from app.core.security import get_user_from_token, get_user

task_router = APIRouter(
    prefix="/task"
)

connected_clients = []  # список клиентов websocket


async def get_task_list(client: WebSocket, session: AsyncSession = Depends(get_async_session)):
    """
    Функция для получения списка всех задач из БД
    :param client: клиент для отправки (websocket)
    :param session: асинхронная сессия
    :return: в цикле передаем клиенту список задач
    """
    from_db = await session.execute(select(Task).order_by(desc(Task.complete), desc(Task.id)))
    task_list = from_db.scalars().all()
    for task in task_list:
        await client.send_text(
            str(task)
        )


@task_router.get("/")
async def get_tasks(
        task_id: int,
        current_user: Annotated[str, Depends(get_user_from_token)],
        session: AsyncSession = Depends(get_async_session)):

    current_task = await session.execute(select(Task).filter(Task.id == task_id))
    task = current_task.scalars().all()[0]
    return str(task)


@task_router.post("/")
async def create_task(
        task: NewTask,
        current_user: Annotated[str, Depends(get_user_from_token)],
        session: AsyncSession = Depends(get_async_session)):

    user = await get_user(current_user, session)
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ошибка права доступа")
    await session.execute(insert(Task), task.model_dump())
    await session.commit()
    for client in connected_clients:
        await client.send_text(f"Пользователь {current_user} добавил задачу: {task.text}")
        await get_task_list(client, session)


@task_router.put("/")
async def update_task(
        task_id: int,
        complete: bool,
        current_user: Annotated[str, Depends(get_user_from_token)],
        session: AsyncSession = Depends(get_async_session),
        ):
    from_db = await session.execute(select(Task).filter(Task.id == task_id))
    current_task = from_db.scalars().all()[0]
    current_task.complete = complete
    session.add(current_task)
    await session.commit()
    for client in connected_clients:
        await client.send_text(f"Пользователь {current_user} обновил задачу № {task_id}")
        await get_task_list(client, session)


@task_router.delete("/")
async def delete_task(
        task_id: int,
        current_user: Annotated[str, Depends(get_user_from_token)],
        session: AsyncSession = Depends(get_async_session)):

    user = await get_user(current_user, session)
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ошибка права доступа")
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
    token = await websocket.receive_text()  # ожидаем отправки токена в websocket
    user = get_user_from_token(token)
    if user is None:    # проверяем, получен ли юзер из полезной нагрузки токена
        await websocket.close(code=1008)
        return
    connected_clients.append(websocket)     # добавляем пользователя в websocket, если токен верен
    await get_task_list(websocket, session)     # передаём пользователю список задач

    try:
        while True:
            await websocket.receive_text()
            await get_task_list(websocket, session)
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
