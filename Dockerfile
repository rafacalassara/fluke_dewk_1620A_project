FROM python:3.13.2-slim

ARG token

RUN apt update && apt install -y git bash gcc python3-dev musl-dev build-essential

WORKDIR /app

COPY . . 

RUN pip install --upgrade pip && \
    pip install uv && \
    uv venv && \
    uv sync 

RUN  . .venv/bin/activate  && python manage.py migrate && python manage.py createsuperuser

EXPOSE 8000
    
ENTRYPOINT [ "sh", "-c", ". .venv/bin/activate && python manage.py runserver 0.0.0.0:8000" ]
