from pydantic import BaseModel
from datetime import timedelta


class NewTask(BaseModel):
    text: str
    complete: bool = False
    execution_time: timedelta = 'P0DT0H30M'     # время на выполнение задачи (30 минут по умолчанию)

