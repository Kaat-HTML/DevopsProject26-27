import os
import sqlite3

from flask import Flask, redirect, render_template_string, request

DB_PATH = os.environ.get("DB_PATH", "/data/backlog.db")
STATUSES = ["backlog", "playing", "done"]

app = Flask(__name__)


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                platform TEXT,
                status TEXT NOT NULL DEFAULT 'backlog'
            )"""
        )


init_db()

PAGE = """
<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Game Backlog</title>
  <style>
    body { font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0;
           max-width: 800px; margin: 40px auto; padding: 0 20px; }
    h1 { color: #60a5fa; }
    form.add { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px; }
    input, select, button { padding: 8px; border-radius: 6px; border: 1px solid #334155;
                            background: #1e293b; color: #e2e8f0; }
    button { cursor: pointer; }
    button:hover { background: #334155; }
    .game { background: #1e293b; border: 1px solid #334155; border-radius: 10px;
            padding: 12px 16px; margin: 10px 0; display: flex;
            justify-content: space-between; align-items: center; gap: 12px; }
    .meta { color: #94a3b8; font-size: 0.9rem; }
    .actions { display: flex; gap: 6px; }
    .actions form { margin: 0; }
  </style>
</head>
<body>
  <h1>Game Backlog</h1>

  <form class="add" method="post" action="/add">
    <input name="title" placeholder="Titel" required maxlength="100">
    <input name="platform" placeholder="Platform (bv. PC)" maxlength="30">
    <button type="submit">Toevoegen</button>
  </form>

  {% for game in games %}
  <div class="game">
    <div>
      <strong>{{ game.title }}</strong>
      <div class="meta">{{ game.platform or "-" }} · {{ game.status }}</div>
    </div>
    <div class="actions">
      <form method="post" action="/status/{{ game.id }}">
        <select name="status" onchange="this.form.submit()">
          {% for s in statuses %}
          <option value="{{ s }}" {% if s == game.status %}selected{% endif %}>{{ s }}</option>
          {% endfor %}
        </select>
      </form>
      <form method="post" action="/delete/{{ game.id }}">
        <button type="submit">Verwijder</button>
      </form>
    </div>
  </div>
  {% else %}
  <p>Nog geen games. Voeg er eentje toe.</p>
  {% endfor %}
</body>
</html>
"""


@app.get("/")
def index():
    with db() as conn:
        games = conn.execute("SELECT * FROM games ORDER BY id DESC").fetchall()
    return render_template_string(PAGE, games=games, statuses=STATUSES)


@app.post("/add")
def add():
    title = request.form.get("title", "").strip()
    platform = request.form.get("platform", "").strip()
    if title:
        with db() as conn:
            conn.execute(
                "INSERT INTO games (title, platform) VALUES (?, ?)", (title, platform)
            )
    return redirect("/")


@app.post("/status/<int:game_id>")
def set_status(game_id):
    status = request.form.get("status")
    if status in STATUSES:
        with db() as conn:
            conn.execute("UPDATE games SET status = ? WHERE id = ?", (status, game_id))
    return redirect("/")


@app.post("/delete/<int:game_id>")
def delete(game_id):
    with db() as conn:
        conn.execute("DELETE FROM games WHERE id = ?", (game_id,))
    return redirect("/")


@app.get("/health")
def health():
    return "ok"