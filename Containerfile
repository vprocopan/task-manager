FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY app.py /app/app.py

ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000
ENV DB_HOST=db
ENV DB_PORT=5432
ENV DB_NAME=tasks
ENV DB_USER=tasks
ENV DB_PASSWORD=tasks

EXPOSE 8000

CMD ["python", "/app/app.py"]
