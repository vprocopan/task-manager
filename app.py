#!/usr/bin/env python3
import os
import sqlite3
from datetime import datetime
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

DB_PATH = os.environ.get("TASK_DB_PATH", "/data/tasks.db")
HOST = os.environ.get("APP_HOST", "0.0.0.0")
PORT = int(os.environ.get("APP_PORT", "8000"))


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def list_tasks(status_filter="all"):
    query = "SELECT id, title, completed, created_at FROM tasks"
    params = ()

    if status_filter == "active":
        query += " WHERE completed = 0"
    elif status_filter == "done":
        query += " WHERE completed = 1"

    query += " ORDER BY id DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return rows


def add_task(title):
    clean = title.strip()
    if not clean:
        return

    now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO tasks (title, completed, created_at) VALUES (?, 0, ?)",
            (clean, now),
        )
        conn.commit()


def toggle_task(task_id):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET completed = CASE WHEN completed = 1 THEN 0 ELSE 1 END
            WHERE id = ?
            """,
            (task_id,),
        )
        conn.commit()


def delete_task(task_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()


def render_page(tasks, status_filter):
    counts = {
        "all": len(tasks),
        "active": sum(1 for t in tasks if t["completed"] == 0),
        "done": sum(1 for t in tasks if t["completed"] == 1),
    }

    filter_options = [
        ("all", "All"),
        ("active", "Active"),
        ("done", "Done"),
    ]

    filters = " ".join(
        (
            f'<a class="tag {"active" if key == status_filter else ""}" href="/?status={key}">{label}</a>'
        )
        for key, label in filter_options
    )

    rows = []
    for task in tasks:
        checked = "checked" if task["completed"] else ""
        state_cls = "done" if task["completed"] else "todo"
        rows.append(
            """
            <li class="task {state_cls}">
                <form method="post" action="/toggle/{id}" class="inline">
                    <button class="toggle" type="submit" title="Toggle task">
                        <input type="checkbox" {checked} onclick="return false" aria-label="toggle">
                    </button>
                </form>
                <span class="title">{title}</span>
                <small>{created_at}</small>
                <form method="post" action="/delete/{id}" class="inline delete-form">
                    <button class="danger" type="submit">Delete</button>
                </form>
            </li>
            """.format(
                state_cls=state_cls,
                id=task["id"],
                checked=checked,
                title=escape(task["title"]),
                created_at=escape(task["created_at"]),
            )
        )

    list_markup = "\n".join(rows) if rows else "<p class='empty'>No tasks yet.</p>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Task Manager</title>
  <style>
    :root {{
      --bg: #f5f7fb;
      --panel: #ffffff;
      --text: #172236;
      --muted: #5f6c82;
      --primary: #0b66ff;
      --danger: #d64545;
      --border: #d6ddea;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      background: linear-gradient(135deg, #eef2ff, #f8fbff);
      color: var(--text);
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 1rem;
    }}
    .card {{
      width: min(860px, 100%);
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.2rem;
      box-shadow: 0 10px 24px rgba(13, 28, 56, 0.08);
    }}
    h1 {{ margin: 0 0 .2rem; }}
    p {{ margin: .2rem 0 1rem; color: var(--muted); }}
    form.add {{ display: flex; gap: .6rem; margin-bottom: 1rem; }}
    input[name="title"] {{
      flex: 1;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: .7rem .8rem;
      font-size: 1rem;
    }}
    button {{
      border: 1px solid transparent;
      border-radius: 10px;
      padding: .65rem .9rem;
      font-weight: 600;
      cursor: pointer;
    }}
    .primary {{ background: var(--primary); color: #fff; }}
    .danger {{ background: #fff; border-color: #f0a9a9; color: var(--danger); }}
    .filters {{ display: flex; gap: .4rem; margin-bottom: .8rem; }}
    .tag {{
      text-decoration: none;
      color: var(--muted);
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: .28rem .62rem;
      font-size: .9rem;
    }}
    .tag.active {{ border-color: var(--primary); color: var(--primary); }}
    ul {{ list-style: none; margin: 0; padding: 0; }}
    .task {{
      display: grid;
      grid-template-columns: auto 1fr auto auto;
      gap: .7rem;
      align-items: center;
      border-bottom: 1px solid #edf1f8;
      padding: .6rem 0;
    }}
    .task .title {{ overflow-wrap: anywhere; }}
    .task.done .title {{ text-decoration: line-through; color: var(--muted); }}
    .inline {{ margin: 0; }}
    .toggle {{ padding: 0; border: none; background: transparent; }}
    .empty {{ color: var(--muted); padding: .8rem 0; }}
    small {{ color: var(--muted); }}
    @media (max-width: 700px) {{
      .task {{ grid-template-columns: auto 1fr auto; }}
      .task small {{ display: none; }}
    }}
  </style>
</head>
<body>
  <main class="card">
    <h1>Task Manager</h1>
    <p>{counts["active"]} active, {counts["done"]} done, {counts["all"]} shown</p>
    <form method="post" action="/add" class="add">
      <input name="title" type="text" maxlength="140" placeholder="Add a task" required>
      <button class="primary" type="submit">Add</button>
    </form>
    <nav class="filters">{filters}</nav>
    <ul>{list_markup}</ul>
  </main>
</body>
</html>
"""


class TaskHandler(BaseHTTPRequestHandler):
    def _redirect_home(self):
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", "/")
        self.end_headers()

    def _parse_form(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        parsed = parse_qs(body, keep_blank_values=True)
        return {k: v[0] if v else "" for k, v in parsed.items()}

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        params = parse_qs(parsed.query)
        status_filter = params.get("status", ["all"])[0]
        if status_filter not in {"all", "active", "done"}:
            status_filter = "all"

        page = render_page(list_tasks(status_filter), status_filter)
        encoded = page.encode("utf-8")

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/add":
            form = self._parse_form()
            add_task(form.get("title", ""))
            self._redirect_home()
            return

        if parsed.path.startswith("/toggle/"):
            task_id = parsed.path.removeprefix("/toggle/")
            if task_id.isdigit():
                toggle_task(int(task_id))
            self._redirect_home()
            return

        if parsed.path.startswith("/delete/"):
            task_id = parsed.path.removeprefix("/delete/")
            if task_id.isdigit():
                delete_task(int(task_id))
            self._redirect_home()
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), TaskHandler)
    print(f"Task manager available at http://{HOST}:{PORT}")
    server.serve_forever()
