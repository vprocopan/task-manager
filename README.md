# Task Manager for Podman

A minimal task manager web app with PostgreSQL persistence, packaged for Podman.

## Features

- Add tasks
- Mark tasks done/active
- Delete tasks
- Filter by status (`all`, `active`, `done`)
- Persist data with PostgreSQL

## Run with Podman

Build the image:

```bash
podman build -t task-manager:latest -f Containerfile .
```

Run with a PostgreSQL container and app container:

```bash
podman run -d --name task-manager-db \
  -e POSTGRES_DB=tasks \
  -e POSTGRES_USER=tasks \
  -e POSTGRES_PASSWORD=tasks \
  -v pg-data:/var/lib/postgresql/data \
  docker.io/library/postgres:16-alpine

podman run --name task-manager -p 8000:8000 --rm \
  -e DB_HOST=host.containers.internal \
  -e DB_PORT=5432 \
  -e DB_NAME=tasks \
  -e DB_USER=tasks \
  -e DB_PASSWORD=tasks \
  task-manager:latest
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

## Run with systemd (user service)

This repo includes `task-manager-compose.service` to run the stack with `podman-compose`.

Install and enable it:

```bash
mkdir -p ~/.config/systemd/user
cp task-manager-compose.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now task-manager-compose.service
```

Check status/logs:

```bash
systemctl --user status task-manager-compose.service
journalctl --user -u task-manager-compose.service -f
```

Stop/disable:

```bash
systemctl --user disable --now task-manager-compose.service
```

Optional: keep the user service running after logout:

```bash
loginctl enable-linger "$USER"
```

## Local run without container

```bash
python3 app.py
```

Configuration via environment variables:

- `APP_HOST` (default: `0.0.0.0`)
- `APP_PORT` (default: `8000`)
- `DATABASE_URL` (optional full DSN, overrides discrete DB vars)
- `DB_HOST` (default: `db`)
- `DB_PORT` (default: `5432`)
- `DB_NAME` (default: `tasks`)
- `DB_USER` (default: `tasks`)
- `DB_PASSWORD` (default: `tasks`)
- `DB_CONNECT_RETRIES` (default: `30`)
- `DB_CONNECT_DELAY_SEC` (default: `1`)
