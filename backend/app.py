import json
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import (
    init_db,
    create_ticket,
    list_tickets,
    list_faq,
    add_faq,
    update_faq,
    delete_faq,
    seed_faq_if_empty,
)

FAQ_PATH = Path(__file__).parent / "faq.json"

ESCALATE_KEYWORDS = [
    "humano", "atendente", "pessoa", "urgente", "reclama", "reclamação",
    "problema", "não resolveu", "não entendi", "falar com atendente", "suporte"
]


class ChatIn(BaseModel):
    message: str


class ChatOut(BaseModel):
    reply: str
    escalated: bool = False
    ticket_id: Optional[int] = None


class FaqIn(BaseModel):
    # keywords separados por |  Ex: "horário|abre|fecha"
    keywords: str
    answer: str


app = FastAPI(title="FarmaBot MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ok no MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# guarda usuários que precisam informar dados antes de abrir ticket
PENDING_CONTACT = {}


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def should_escalate(msg: str) -> bool:
    m = normalize(msg)
    return any(k in m for k in ESCALATE_KEYWORDS)


def load_faq_json():
    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_faq_items_from_db_or_seed():
    """
    Fonte principal = banco.
    Se banco estiver vazio, faz seed a partir do faq.json.
    """
    default_items = load_faq_json()
    seed_faq_if_empty(default_items)
    return list_faq()


def best_faq_answer(msg: str):
    m = normalize(msg)
    best = None
    best_score = 0

    # Agora o FAQ vem do banco
    faq_items = get_faq_items_from_db_or_seed()

    for item in faq_items:
        score = 0
        # keywords vem como string "a|b|c"
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


@app.on_event("startup")
def startup():
    init_db()
    # Garante que o banco tenha FAQ (seed se estiver vazio)
    get_faq_items_from_db_or_seed()


@app.post("/chat", response_model=ChatOut)
def chat(payload: ChatIn):
    msg = payload.message.strip()
    if not msg:
        return ChatOut(reply="Pode me dizer como posso ajudar? 😊")

    user_id = "default"  # MVP simples (depois vira sessão/IP)

    # Se estamos aguardando nome/telefone
    if user_id in PENDING_CONTACT:
        name = None
        phone = None

        # Remove tudo que não é número
        digits = re.sub(r"\D", "", msg)

        # Remove DDI do Brasil se vier (+55)
        if digits.startswith("55") and len(digits) in (12, 13):
            digits = digits[2:]

        # Se tiver tamanho plausível, considera telefone
        if len(digits) in (8, 9, 10, 11):
            phone = digits

        # Extrai nome removendo o telefone digitado
        name_candidate = msg
        if phone:
            name_candidate = re.sub(re.escape(digits), "", name_candidate)

        name_candidate = re.sub(r"[-() +]+", " ", name_candidate).strip()

        if name_candidate:
            name = name_candidate

        data = PENDING_CONTACT.pop(user_id)
        tid = create_ticket(name, phone, data["message"])

        return ChatOut(
            reply=f"Obrigado! Encaminhei seu atendimento para um atendente humano 😊 (Ticket #{tid})",
            escalated=True,
            ticket_id=tid
        )

    # Pedido explícito de humano
    if should_escalate(msg):
        PENDING_CONTACT[user_id] = {"message": msg}
        return ChatOut(
            reply="Certo! Para te encaminhar, pode me informar seu *nome* e *telefone*? 😊"
        )

    # Tenta responder pela FAQ (agora via banco)
    answer, _ = best_faq_answer(msg)
    if answer:
        return ChatOut(reply=answer)

    # Fallback: não entendeu → pede contato
    PENDING_CONTACT[user_id] = {"message": msg}
    return ChatOut(
        reply="Não consegui te ajudar com isso agora. Pode me informar seu *nome* e *telefone* para eu encaminhar a um atendente? 😊"
    )


@app.get("/tickets")
def tickets(limit: int = 50):
    return {"tickets": list_tickets(limit=limit)}


# -------------------------
# FAQ (editável via banco)
# -------------------------
@app.get("/faq")
def get_faq():
    # garante seed se estiver vazio e retorna lista
    return {"faq": get_faq_items_from_db_or_seed()}


@app.post("/faq")
def create_faq(payload: FaqIn):
    faq_id = add_faq(payload.keywords.strip(), payload.answer.strip())
    return {"ok": True, "id": faq_id}

@app.put("/faq/{faq_id}")
def edit_faq(faq_id: int, payload: FaqIn):
    ok = update_faq(faq_id, payload.keywords.strip(), payload.answer.strip())
    return {"ok": ok}


@app.delete("/faq/{faq_id}")
def remove_faq(faq_id: int):
    ok = delete_faq(faq_id)
    return {"ok": ok}
