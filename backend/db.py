import psycopg2
import os

def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# =========================
# INIT DATABASE
# =========================

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id SERIAL PRIMARY KEY,
        slug TEXT UNIQUE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id SERIAL PRIMARY KEY,
        company_id INTEGER,
        name TEXT,
        phone TEXT,
        message TEXT,
        status TEXT DEFAULT 'open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS faq (
        id SERIAL PRIMARY KEY,
        company_id INTEGER,
        keywords TEXT,
        answer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

# =========================
# COMPANY
# =========================

def get_or_create_company(slug):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM companies WHERE slug=%s", (slug,))
    row = cur.fetchone()

    if row:
        cur.close()
        conn.close()
        return row[0]

    cur.execute("INSERT INTO companies (slug) VALUES (%s) RETURNING id", (slug,))
    company_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return company_id

# =========================
# TICKETS
# =========================

def create_ticket(company_id, name, phone, message):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO tickets (company_id, name, phone, message)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (company_id, name, phone, message))

    ticket_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return ticket_id

def list_tickets(company_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, created_at, name, phone, message, status
        FROM tickets
        WHERE company_id=%s
        ORDER BY id DESC
    """, (company_id,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows

# =========================
# FAQ
# =========================

def add_faq(company_id, keywords, answer):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO faq (company_id, keywords, answer)
        VALUES (%s, %s, %s)
    """, (company_id, keywords, answer))

    conn.commit()
    cur.close()
    conn.close()

def list_faq(company_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, keywords, answer, created_at
        FROM faq
        WHERE company_id=%s
        ORDER BY id DESC
    """, (company_id,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    # transforma em dict (compatível com seu código atual)
    return [
        {
            "id": r[0],
            "keywords": r[1],
            "answer": r[2],
            "created_at": r[3]
        }
        for r in rows
    ]