import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "tickets.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                name TEXT,
                phone TEXT,
                message TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
        conn.commit()

def create_ticket(name: str | None, phone: str | None, message: str) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tickets (created_at, name, phone, message, status) VALUES (?, ?, ?, ?, ?)",
            (datetime.utcnow().isoformat(), name, phone, message, "open")
        )
        conn.commit()
        return cur.lastrowid

def list_tickets(limit: int = 50):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, created_at, name, phone, message, status FROM tickets ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "created_at": r[1],
            "name": r[2],
            "phone": r[3],
            "message": r[4],
            "status": r[5],
        }
        for r in rows
    ]
