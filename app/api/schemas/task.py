from pydantic import BaseModel


class NewTask(BaseModel):
    text: str
    complete: bool = False

