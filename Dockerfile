FROM python:3.13.2-slim

ARG token

RUN apt update && apt install -y git bash gcc python3-dev musl-dev build-essential

WORKDIR /app

RUN git clone https://github.com/rafacalassara/fluke_dewk_1620A_project.git .

RUN pip install --upgrade pip && \
    pip install uv && \
    uv venv && \
    . .venv/bin/activate && \
    uv sync

COPY .env .env
COPY db.sqlite3 db.sqlite3    

EXPOSE 8000
    
ENTRYPOINT [ "sh", "-c", ". .venv/bin/activate && python manage.py runserver 0.0.0.0:8000" ]



