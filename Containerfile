FROM python:3.12-slim

WORKDIR /app
COPY app.py /app/app.py

ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000
ENV TASK_DB_PATH=/data/tasks.db

EXPOSE 8000
VOLUME ["/data"]

CMD ["python", "/app/app.py"]
