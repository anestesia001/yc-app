import os
from flask import Flask, request, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 5432)),
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )

def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
        conn.commit()
    finally:
        conn.close()

@app.route("/", methods=["GET"])
def index():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, text, created_at FROM messages ORDER BY created_at DESC LIMIT 50")
            rows = cur.fetchall()
    finally:
        conn.close()

    html = """
    <!doctype html>
    <html>
    <head><meta charset="utf-8"><title>Messages</title></head>
    <body>
      <h1>Messages</h1>
      <form method="post" action="/">
        <input name="text" required placeholder="Message text">
        <button type="submit">Send</button>
      </form>
      <ul>
    """
    for r in rows:
        html += f"<li>{r['text']} — {r['created_at']}</li>"
    html += """
      </ul>
    </body>
    </html>
    """
    return html

@app.route("/", methods=["POST"])
def add_message():
    text = request.form.get("text", "").strip()
    if not text:
        return redirect(url_for("index"))
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO messages (text) VALUES (%s)", (text,))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
