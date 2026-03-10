import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "tickets.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # empresas
    cur.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # FAQ por empresa
    cur.execute("""
    CREATE TABLE IF NOT EXISTS faq (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        keywords TEXT NOT NULL,
        answer TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(company_id) REFERENCES companies(id)
    )
    """)

    # tickets por empresa
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        name TEXT,
        phone TEXT,
        message TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY(company_id) REFERENCES companies(id)
    )
    """)

    conn.commit()
    conn.close()


# -------------------------
# empresas
# -------------------------

def get_company_by_slug(slug: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, slug, name FROM companies WHERE slug=?",
        (slug,)
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "slug": row[1],
        "name": row[2]
    }


def create_company(slug: str, name: str):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO companies (slug, name, created_at) VALUES (?, ?, ?)",
        (slug, name, datetime.utcnow().isoformat())
    )

    conn.commit()
    company_id = cur.lastrowid
    conn.close()

    return company_id


def get_or_create_company(slug: str):

    company = get_company_by_slug(slug)

    if company:
        return company["id"]

    return create_company(slug, slug.capitalize())


# -------------------------
# FAQ
# -------------------------

def list_faq(company_id: int):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, keywords, answer FROM faq WHERE company_id=? ORDER BY id DESC",
        (company_id,)
    )

    rows = cur.fetchall()
    conn.close()

    return [
        {"id": r[0], "keywords": r[1], "answer": r[2]}
        for r in rows
    ]


def add_faq(company_id: int, keywords: str, answer: str):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO faq (company_id, keywords, answer, created_at) VALUES (?, ?, ?, ?)",
        (company_id, keywords, answer, datetime.utcnow().isoformat())
    )

    conn.commit()
    faq_id = cur.lastrowid
    conn.close()

    return faq_id


# -------------------------
# tickets
# -------------------------

def create_ticket(company_id: int, name: str | None, phone: str | None, message: str):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO tickets (company_id, created_at, name, phone, message, status) VALUES (?, ?, ?, ?, ?, ?)",
        (
            company_id,
            datetime.utcnow().isoformat(),
            name,
            phone,
            message,
            "open"
        )
    )

    conn.commit()
    ticket_id = cur.lastrowid
    conn.close()

    return ticket_id


def list_tickets(company_id: int, limit: int = 50):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, created_at, name, phone, message, status
        FROM tickets
        WHERE company_id=?
        ORDER BY id DESC
        LIMIT ?
        """,
        (company_id, limit)
    )

    rows = cur.fetchall()
    conn.close()

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
