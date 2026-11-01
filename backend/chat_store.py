"""Small SQLite store for KrishiMitra chat sessions."""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "krishimitra_chat.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY, title TEXT NOT NULL, updated_at TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(chat_id) REFERENCES chats(id)
    )""")
    conn.commit()
    return conn


def create_chat(chat_id, title="New chat"):
    with _connect() as conn:
        conn.execute("INSERT OR REPLACE INTO chats(id,title,updated_at) VALUES(?,?,?)",
                     (chat_id, title, datetime.now().isoformat(timespec="seconds")))


def add_message(chat_id, role, content):
    with _connect() as conn:
        exists = conn.execute("SELECT 1 FROM chats WHERE id=?", (chat_id,)).fetchone()
        if not exists:
            create_chat(chat_id)
        conn.execute("INSERT INTO messages(chat_id,role,content,created_at) VALUES(?,?,?,?)",
                     (chat_id, role, content, datetime.now().isoformat(timespec="seconds")))
        if role == "user":
            title = content.strip().replace("\n", " ")[:55] or "New chat"
            conn.execute("UPDATE chats SET title=?,updated_at=? WHERE id=?",
                         (title, datetime.now().isoformat(timespec="seconds"), chat_id))
        else:
            conn.execute("UPDATE chats SET updated_at=? WHERE id=?",
                         (datetime.now().isoformat(timespec="seconds"), chat_id))


def list_chats(limit=30):
    with _connect() as conn:
        rows = conn.execute("SELECT id,title,updated_at FROM chats ORDER BY updated_at DESC LIMIT ?",
                            (limit,)).fetchall()
    return [{"id": r[0], "title": r[1], "updated_at": r[2]} for r in rows]


def get_messages(chat_id):
    with _connect() as conn:
        rows = conn.execute("SELECT role,content FROM messages WHERE chat_id=? ORDER BY id", (chat_id,)).fetchall()
    return [{"role": r[0], "content": r[1]} for r in rows]


def delete_chat(chat_id):
    with _connect() as conn:
        conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
        conn.execute("DELETE FROM chats WHERE id=?", (chat_id,))


def clear_messages(chat_id):
    with _connect() as conn:
        conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
        conn.execute("UPDATE chats SET title=?,updated_at=? WHERE id=?",
                     ("New chat", datetime.now().isoformat(timespec="seconds"), chat_id))
