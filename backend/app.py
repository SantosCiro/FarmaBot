import json
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import init_db, create_ticket, list_tickets

# --------------------
# Carrega FAQ
# --------------------
FAQ_PATH = Path(__file__).parent / "faq.json"


def load_faq():
    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


FAQ = load_faq()

# Guarda usuários aguardando contato
PENDING_CONTACT = {}

ESCALATE_KEYWORDS = [
    "humano", "atendente", "pessoa", "urgente", "reclama", "reclamação",
    "problema", "não resolveu", "não entendi", "falar com atendente", "suporte"
]

# --------------------
# Modelos
# --------------------
class ChatIn(BaseModel):
    message: str


class ChatOut(BaseModel):
    reply: str
    escalated: bool = False
    ticket_id: Optional[int] = None


# --------------------
# App
# --------------------
app = FastAPI(title="FarmaBot MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


# --------------------
# Helpers
# --------------------
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


# --------------------
# Endpoints
# --------------------
@app.post("/chat", response_model=ChatOut)
def chat(payload: ChatIn):
    msg = payload.message.strip()
    if not msg:
        return ChatOut(reply="Pode me dizer como posso ajudar? 😊")

    user_id = "default"  # MVP simples

    # ============================
    # Aguardando nome / telefone
    # ============================
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

    # ============================
    # Pedido explícito de humano
    # ============================
    if should_escalate(msg):
        PENDING_CONTACT[user_id] = {"message": msg}
        return ChatOut(
            reply="Certo! Para te encaminhar, pode me informar seu *nome* e *telefone*? 😊"
        )

    # ============================
    # FAQ
    # ============================
    answer, _ = best_faq_answer(msg)
    if answer:
        return ChatOut(reply=answer)

    # ============================
    # Fallback
    # ============================
    PENDING_CONTACT[user_id] = {"message": msg}
    return ChatOut(
        reply="Não consegui te ajudar com isso agora. Pode me informar seu *nome* e *telefone* para eu encaminhar a um atendente? 😊"
    )


@app.get("/tickets")
def tickets(limit: int = 50):
    return {"tickets": list_tickets(limit=limit)}
