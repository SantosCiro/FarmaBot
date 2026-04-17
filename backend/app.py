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
    update_ticket_status,
    list_faq,
    add_faq,
    delete_faq,
)

client = OpenAI()
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

ESCALATE_KEYWORDS = [
    "humano", "atendente", "pessoa", "urgente", "reclama", "reclamacao",
    "problema", "nao resolveu", "nao entendi", "falar com atendente", "suporte"
]

PRODUCT_KEYWORDS = [
    "tem ", "voce tem", "voces tem", "tem o", "tem a", "tem os", "tem as",
    "possui", "disponivel", "disponibilidade", "medicamento", "remedio",
    "frasco", "caixa", "dorflex", "dipirona", "paracetamol", "clonazepam",
    "fralda", "pomada", "xarope"
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


class TicketStatusIn(BaseModel):
    status: str


app = FastAPI(title="FarmaBot MVP")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PENDING_CONTACT = {}


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"\s+", " ", text)
    return text


def should_escalate(msg: str) -> bool:
    m = normalize(msg)
    return any(k in m for k in ESCALATE_KEYWORDS)


def is_product_question(msg: str) -> bool:
    m = normalize(msg)
    return any(k in m for k in PRODUCT_KEYWORDS)


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
Você é um atendente virtual de farmácia.

Use apenas as informações abaixo para responder:

{faq_text}

Regras:
- Responda apenas dúvidas gerais da farmácia.
- Não confirme disponibilidade de medicamentos ou produtos.
- Se a pergunta for sobre estoque, produto, medicamento ou preço, diga que precisa encaminhar para um atendente.
- Se a resposta não estiver no FAQ, diga que não tem essa informação e ofereça encaminhar para um atendente.
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

    # 1. fluxo de coleta de contato
    if user_id in PENDING_CONTACT:
        data = PENDING_CONTACT[user_id]
        digits = re.sub(r"\D", "", msg)

        if not data.get("name") and len(digits) < 8:
            data["name"] = msg.strip()
            return ChatOut(
                reply="Perfeito! Agora preciso do seu *telefone* 😊"
            )

        if len(digits) >= 8:
            phone = digits

            if phone.startswith("55") and len(phone) in (12, 13):
                phone = phone[2:]

            name = data.get("name") or "Cliente"
            original_message = data["message"]

            PENDING_CONTACT.pop(user_id)

            tid = create_ticket(company_id, name, phone, original_message)

            return ChatOut(
                reply=f"Obrigado! Encaminhei seu atendimento para um atendente humano 😊 (Ticket #{tid})",
                escalated=True,
                ticket_id=tid
            )

        return ChatOut(
            reply="Pode me informar seu *telefone* para continuar? 😊"
        )

    # 2. perguntas de produto/medicamento vão para humano
    if is_product_question(msg):
        PENDING_CONTACT[user_id] = {"message": msg}
        return ChatOut(
            reply="Para confirmar disponibilidade de medicamento ou produto, preciso encaminhar seu atendimento para a equipe. Pode me informar seu *nome* e *telefone*? 😊"
        )

    # 3. pedido explícito de humano
    if should_escalate(msg):
        PENDING_CONTACT[user_id] = {"message": msg}
        return ChatOut(
            reply="Certo! Para te encaminhar, pode me informar seu *nome* e *telefone*? 😊"
        )

    # 4. FAQ
    answer, _ = best_faq_answer(company_id, msg)
    if answer:
        return ChatOut(reply=answer)

    # 5. IA
    ai_reply = ai_answer(company_id, msg)
    if ai_reply:
        return ChatOut(reply=ai_reply)

    # 6. fallback
    return ChatOut(
        reply="Não consegui te ajudar com essa dúvida agora. Se quiser, posso encaminhar para um atendente 😊"
    )


@app.get("/{company_slug}/tickets")
def tickets(company_slug: str):
    company_id = get_or_create_company(company_slug)
    return {"tickets": list_tickets(company_id)}


@app.put("/{company_slug}/tickets/{ticket_id}/status")
def ticket_status(company_slug: str, ticket_id: int, payload: TicketStatusIn):
    status = payload.status.strip().lower()

    if status not in ("open", "closed"):
        return {"ok": False, "error": "invalid_status"}

    get_or_create_company(company_slug)
    ok = update_ticket_status(ticket_id, status)
    return {"ok": ok}


@app.get("/{company_slug}/faq")
def get_faq(company_slug: str):
    company_id = get_or_create_company(company_slug)
    return {"faq": list_faq(company_id)}


@app.post("/{company_slug}/faq")
def create_faq(company_slug: str, payload: FaqIn):
    company_id = get_or_create_company(company_slug)
    faq_id = add_faq(company_id, payload.keywords.strip(), payload.answer.strip())
    return {"ok": True, "id": faq_id}


@app.delete("/faq/{faq_id}")
def remove_faq(faq_id: int):
    ok = delete_faq(faq_id)
    return {"ok": ok}


@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/tickets.html")
def tickets_page():
    return FileResponse(FRONTEND_DIR / "tickets.html")


@app.get("/faq.html")
def faq_page():
    return FileResponse(FRONTEND_DIR / "faq.html")