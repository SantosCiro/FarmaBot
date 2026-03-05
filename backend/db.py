import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "tickets.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        # Tabela de tickets
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

        # Tabela de FAQ (editável)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keywords TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
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


# ---------------------------
# FAQ (Banco)
# keywords fica tipo: "horário|abre|fecha"
# ---------------------------
def list_faq():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, keywords, answer, created_at FROM faq ORDER BY id DESC")
        rows = cur.fetchall()

    return [
        {"id": r[0], "keywords": r[1], "answer": r[2], "created_at": r[3]}
        for r in rows
    ]


def add_faq(keywords: str, answer: str) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO faq (keywords, answer) VALUES (?, ?)",
            (keywords, answer)
        )
        conn.commit()
        return cur.lastrowid

def update_faq(faq_id: int, keywords: str, answer: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE faq SET keywords = ?, answer = ? WHERE id = ?",
            (keywords, answer, faq_id)
        )
        conn.commit()
        return cur.rowcount > 0

def delete_faq(faq_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM faq WHERE id = ?", (faq_id,))
        conn.commit()
        return cur.rowcount > 0

def seed_faq_if_empty(default_faq_items: list[dict]):
    """
    default_faq_items: lista com dicts no formato:
    {"keywords": ["a","b"], "resposta": "texto"}
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM faq")
        count = cur.fetchone()[0]

        if count == 0:
            for item in default_faq_items:
                keywords = "|".join(item.get("keywords", []))
                answer = item.get("resposta", "")
                cur.execute(
                    "INSERT INTO faq (keywords, answer) VALUES (?, ?)",
                    (keywords, answer)
                )
            conn.commit()