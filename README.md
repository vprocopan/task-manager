# Task Manager for Podman

A minimal task manager web app with SQLite persistence, packaged for Podman.

## Features

- Add tasks
- Mark tasks done/active
- Delete tasks
- Filter by status (`all`, `active`, `done`)
- Persist data with a Podman volume

## Run with Podman

Build the image:

```bash
podman build -t task-manager:latest -f Containerfile .
```

Run the container:

```bash
podman run --name task-manager -p 8000:8000 -v task-data:/data --rm task-manager:latest
```

Open: http://localhost:8000

## Run with podman-compose

```bash
podman-compose up --build
```

Stop:

```bash
podman-compose down
```

## Local run without container

```bash
python3 app.py
```

Configuration via environment variables:

- `APP_HOST` (default: `0.0.0.0`)
- `APP_PORT` (default: `8000`)
- `TASK_DB_PATH` (default: `/data/tasks.db`)
