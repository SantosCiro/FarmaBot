import json
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import init_db, create_ticket, list_tickets

FAQ_PATH = Path(__file__).parent / "faq.json"

def load_faq():
    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

FAQ = load_faq()
# guarda usuários que precisam informar dados antes de abrir ticket
PENDING_CONTACT = {}

ESCALATE_KEYWORDS = [
    "humano", "atendente", "pessoa", "urgente", "reclama", "reclamação",
    "problema", "não resolveu", "não entendi", "falar com atendente", "suporte"
]

MEDICAL_DISCLAIMER = (
    "⚠️ Importante: sou um assistente virtual de atendimento. "
    "Não realizo diagnóstico nem indico medicamentos. "
    "Se for emergência, procure atendimento médico imediatamente."
)

class ChatIn(BaseModel):
    message: str

class ChatOut(BaseModel):
    reply: str
    escalated: bool = False
    ticket_id: Optional[int] = None

app = FastAPI(title="FarmaBot MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ok no MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text

def should_escalate(msg: str) -> bool:
    m = normalize(msg)
    return any(k in m for k in ESCALATE_KEYWORDS)

def best_faq_answer(msg: str):
    m = normalize(msg)
    best = None
    best_score = 0

    for item in FAQ:
        score = 0
        for kw in item.get("keywords", []):
            if kw in m:
                score += 1
        if score > best_score:
            best_score = score
            best = item

    if best and best_score >= 1:
        return best["resposta"], best_score
    return None, 0

@app.post("/chat", response_model=ChatOut)
def chat(payload: ChatIn):
    msg = payload.message.strip()
    if not msg:
        return ChatOut(reply="Pode me dizer como posso ajudar? 😊")

    user_id = "default"  # MVP simples (depois vira sessão/IP)

    # Se estamos aguardando nome/telefone
    if user_id in PENDING_CONTACT:
        text = normalize(msg)
        name = None
        phone = None

        # tentativa simples de extrair telefone
        import re
        m = re.search(r"(\d{8,13})", text)
        if m:
            phone = m.group(1)

        # se não veio telefone, assume que é nome
        if not phone:
            name = msg.strip()

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

    # Tenta responder pela FAQ
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
