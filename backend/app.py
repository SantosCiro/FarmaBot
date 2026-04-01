import json
import re
import unicodedata

from openai import OpenAI
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from db import (
    init_db,
    get_or_create_company,
    create_ticket,
    list_tickets,
    list_faq,
    add_faq,
)

client = OpenAI()
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

ESCALATE_KEYWORDS = [
    "humano", "atendente", "pessoa", "urgente", "reclama", "reclamação",
    "problema", "não resolveu", "não entendi", "falar com atendente", "suporte"
]


class ChatIn(BaseModel):
    message: str
    name: Optional[str] = None
    phone: Optional[str] = None


class ChatOut(BaseModel):
    reply: str
    escalated: bool = False
    ticket_id: Optional[int] = None


class FaqIn(BaseModel):
    keywords: str
    answer: str


app = FastAPI(title="FarmaBot MVP")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# guarda usuários que precisam informar dados antes de abrir ticket
PENDING_CONTACT = {}


def normalize(text: str) -> str:
    text = text.lower().strip()

    # remove acentos
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # remove espaços extras
    text = re.sub(r"\s+", " ", text)

    return text


def should_escalate(msg: str) -> bool:
    m = normalize(msg)
    return any(k in m for k in ESCALATE_KEYWORDS)


def best_faq_answer(company_id: int, msg: str):
    m = normalize(msg)
    best = None
    best_score = 0

    faq_items = list_faq(company_id)

    for item in faq_items:
        score = 0
        kws = [k.strip() for k in (item.get("keywords") or "").split("|") if k.strip()]

        for kw in kws:
            if normalize(kw) in m:
                score += 1

        if score > best_score:
            best_score = score
            best = item

    if best and best_score >= 1:
        return best["answer"], best_score

    return None, 0

def ai_answer(company_id: int, message: str) -> str:
    try:
        faq_items = list_faq(company_id)

        faq_text = "FAQ da farmácia:\n"
        for item in faq_items:
            faq_text += f"- {item['keywords']}: {item['answer']}\n"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""
Você é um atendente de farmácia.

Use apenas as informações abaixo para responder:

{faq_text}

Se a resposta não estiver no FAQ, diga que não tem essa informação e ofereça encaminhar para um atendente.
"""
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:
        print("ERRO IA:", e)
        return None

@app.on_event("startup")
def startup():
    init_db()


@app.post("/{company_slug}/chat", response_model=ChatOut)
def chat(company_slug: str, payload: ChatIn):
    msg = payload.message.strip()
    company_id = get_or_create_company(company_slug)

    if not msg:
        return ChatOut(reply="Pode me dizer como posso ajudar? 😊")

    user_id = company_slug

    # =========================
    # 1. Se está aguardando contato
    # =========================
    if user_id in PENDING_CONTACT:
        digits = re.sub(r"\D", "", msg)

        # =========================
        # TEM TELEFONE → cria ticket
        # =========================
        if len(digits) >= 8:
            name = payload.name
            phone = digits

            if phone.startswith("55") and len(phone) in (12, 13):
                phone = phone[2:]

            name_candidate = re.sub(r"\d+", "", msg)
            name_candidate = re.sub(r"[-() +]+", " ", name_candidate).strip()

            if name_candidate:
                name = name_candidate

            data = PENDING_CONTACT.pop(user_id)
            tid = create_ticket(company_id, name, phone, data["message"])

            return ChatOut(
                reply=f"Obrigado! Encaminhei seu atendimento para um atendente humano 😊 (Ticket #{tid})",
                escalated=True,
                ticket_id=tid
            )

        # =========================
        # NÃO TEM TELEFONE → pede
        # =========================
        return ChatOut(
            reply="Preciso também do seu *telefone* para continuar, ok? 😊"
        )

    # =========================
    # 2. ESCALAR (ANTES DE TUDO)
    # =========================
    if should_escalate(msg):
        PENDING_CONTACT[user_id] = {"message": msg}
        return ChatOut(
            reply="Certo! Para te encaminhar, pode me informar seu *nome* e *telefone*? 😊"
        )

    # =========================
    # 3. FAQ
    # =========================
    answer, _ = best_faq_answer(company_id, msg)
    if answer:
        return ChatOut(reply=answer)

    # =========================
    # 4. IA
    # =========================
    ai_reply = ai_answer(company_id, msg)
    if ai_reply:
        return ChatOut(reply=ai_reply)


@app.get("/{company_slug}/tickets")
def tickets(company_slug: str, limit: int = 50):
    company_id = get_or_create_company(company_slug)
    return {"tickets": list_tickets(company_id)}


@app.get("/{company_slug}/faq")
def get_faq(company_slug: str):
    company_id = get_or_create_company(company_slug)
    return {"faq": list_faq(company_id)}


@app.post("/{company_slug}/faq")
def create_faq(company_slug: str, payload: FaqIn):
    company_id = get_or_create_company(company_slug)
    faq_id = add_faq(company_id, payload.keywords.strip(), payload.answer.strip())
    return {"ok": True, "id": faq_id}

@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/tickets.html")
def tickets_page():
    return FileResponse(FRONTEND_DIR / "tickets.html")


@app.get("/faq.html")
def faq_page():
    return FileResponse(FRONTEND_DIR / "faq.html")