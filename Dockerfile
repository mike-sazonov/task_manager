FROM python:3.11.6

WORKDIR ./
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN pip install pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system
COPY . .
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
