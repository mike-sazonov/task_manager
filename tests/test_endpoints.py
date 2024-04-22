import pytest
from fastapi.testclient import TestClient

from datetime import datetime as dt, timedelta as td

from main import app
from app.db.database import get_async_session
from .db_test import get_test_async_session, drop_test_db


client = TestClient(app)


class TestDB:
    test_token = {}

    app.dependency_overrides[get_async_session] = get_test_async_session

    # регистрация админа
    @pytest.mark.asyncio
    async def test_reg_admin_user(self):
        data = {"username": "Admin", "password": "test", "role": "admin"}
        response = client.post(
            "/user/registrate",
            json=data)
        assert response.status_code == 200
        assert response.json() == {"message": f"Пользователь {data['username']} успешно зарегистрирован"}

    # регистрация базового юзера
    @pytest.mark.asyncio
    async def test_reg_base_user(self):
        data = {"username": "Base", "password": "base"}
        response = client.post(
            "/user/registrate",
            json=data)
        assert response.status_code == 200
        assert response.json() == {"message": f"Пользователь {data['username']} успешно зарегистрирован"}

    # аутентификация админа
    @pytest.mark.asyncio
    async def test_login_admin_user(self):
        data = {"username": "Admin", "password": "test"}
        response = client.post(
            "/user/login",
            data=data,
            headers={"content-type": "application/x-www-form-urlencoded"})
        assert response.status_code == 200
        response_data = response.json()
        assert "access_token" in response_data
        self.test_token["admin_token"] = response.json()["access_token"]

    # аутентификация базового юзера
    @pytest.mark.asyncio
    async def test_login_base_user(self):
        data = {"username": "Base", "password": "base"}
        response = client.post(
            "/user/login",
            data=data,
            headers={"content-type": "application/x-www-form-urlencoded"})
        assert response.status_code == 200
        response_data = response.json()
        assert "access_token" in response_data
        self.test_token["base_token"] = response.json()["access_token"]

    # добавление новой задачи админом
    @pytest.mark.asyncio
    async def test_post_task_admin(self):
        data = {"text": "test_task", "complete": False, "execution_time": "P0DT0H30M"}
        token = self.test_token["admin_token"]
        response = client.post("/task/", json=data, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

    # попытка добавления новой задачи базовым юзером
    @pytest.mark.asyncio
    async def test_post_task_base(self):
        data = {"text": "test_task", "complete": False, "execution_time": "P0DT0H30M"}
        token = self.test_token["base_token"]
        response = client.post("/task/", json=data, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    # получение задачи
    @pytest.mark.asyncio
    async def test_get_task(self):
        task_time = dt.strftime(dt.now() + td(minutes=30), '%d.%m.%y %H:%M')
        token = self.test_token["admin_token"]
        response = client.get("/task/?task_id=1", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert (response.json() ==
                f"Задача №1, test_task, Выполнить до: {task_time}, статус: Не выполнена")

    # обновление задачи
    @pytest.mark.asyncio
    async def test_put_task(self):
        token = self.test_token["admin_token"]
        response = client.put("/task/?task_id=1&complete=True", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        current_task = client.get("/task/?task_id=1", headers={"Authorization": f"Bearer {token}"})
        assert current_task.json().split(', ')[-1] == "статус: Выполнена"

    # попытка удаления задачи базовым юзером
    @pytest.mark.asyncio
    async def test_delete_task_base(self):
        token = self.test_token["base_token"]
        response = client.delete("/task/?task_id=1", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    # удаление задачи админом
    @pytest.mark.asyncio
    async def test_delete_task_admin(self):
        token = self.test_token["admin_token"]
        response = client.delete("/task/?task_id=1", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_finish(self):
        await drop_test_db()
