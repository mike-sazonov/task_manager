import datetime as dt
from sqlalchemy import Integer, DateTime, func, Interval
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str]
    password: Mapped[str]
    role: Mapped[str] = mapped_column(nullable=True)


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    text: Mapped[str]
    complete: Mapped[bool] = mapped_column(default=False)
    create_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=True, server_default=func.now())
    execution_time: Mapped[dt.timedelta] = mapped_column(Interval, nullable=True)

    def complete_date(self):
        return self.create_at + self.execution_time

    def is_act_task(self):
        return self.complete_date() > dt.datetime.now()

    def __str__(self):
        return (f"Задача №{self.id}, {self.text},"
                f" Выполнить до: "
                f"{('просрочено', dt.datetime.strftime(self.complete_date(), '%d.%m.%y %H:%M'))[self.is_act_task()]},"
                f" статус: {('Не выполнена', 'Выполнена')[self.complete]}")

