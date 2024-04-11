import uvicorn
from fastapi import FastAPI

from app.api.endpoints.users import user_router
from app.api.endpoints.tasks import task_router


app = FastAPI()

app.include_router(user_router)
app.include_router(task_router)


if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True)
