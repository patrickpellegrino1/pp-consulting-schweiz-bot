import os
import json
import smtplib
from email.message import EmailMessage
from typing import List, Optional, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

from bot_config import SYSTEM_PROMPT, COMPANY
from db import init_db, save_lead

load_dotenv()
client = OpenAI()

app = FastAPI(title="PP Consulting LeadBot")

# Wix / Browser Calls -> CORS needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # später auf deine Wix-Domain einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

class ChatTurn(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    conversation: List[ChatTurn]

class ChatResponse(BaseModel):
    reply: str
    lead_saved: bool = False
    lead_id: Optional[int] = None

def maybe_send_email(subject: str, body: str) -> bool:
    host = os.getenv("SMTP_HOST", "").strip()
    if not host:
        return False
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    pw = os.getenv("SMTP_PASS", "")
    to = os.getenv("SMTP_TO", COMPANY["email"])
    from_addr = os.getenv("SMTP_FROM", "leadbot@pp-consulting-schweiz.ch")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    msg.set_content(body)

    with smtplib.SMTP(host, port) as s:
        s.starttls()
        if user:
            s.login(user, pw)
        s.send_message(msg)
    return True

LEAD_SCHEMA = {
    "name": "lead_intake",
    "schema": {
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": ["lead", "question", "other"]},
            "lead": {
                "type": ["object", "null"],
                "properties": {
                    "name": {"type": ["string", "null"]},
                    "company": {"type": ["string", "null"]},
                    "industry": {"type": ["string", "null"]},
                    "goal": {"type": ["string", "null"]},
                    "status": {"type": ["string", "null"]},
                    "budget": {"type": ["string", "null"]},
                    "timeline": {"type": ["string", "null"]},
                    "contact": {"type": ["string", "null"]},
                    "notes": {"type": ["string", "null"]}
                },
                "required": ["name","company","industry","goal","status","budget","timeline","contact","notes"]
            },
            "missing_fields": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["intent","lead","missing_fields"]
    }
}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT.strip()}]
    for t in req.conversation[-20:]:
        messages.append({"role": t.role, "content": t.content})

    # 1) user-facing answer
    resp = client.responses.create(
        model="gpt-4.1-mini",
        input=messages,
        max_output_tokens=320,
    )

    reply_parts = []
    for out in resp.output:
        if out.type == "message":
            for c in out.content:
                if c.type == "output_text":
                    reply_parts.append(c.text)
    reply_text = "\n".join(reply_parts).strip() or "Entschuldigung, da ist etwas schiefgelaufen."

    # 2) structured lead extraction
    extract = client.responses.create(
        model="gpt-4.1-mini",
        input=messages,
        response_format={"type": "json_schema", "json_schema": LEAD_SCHEMA},
        max_output_tokens=220,
    )

    extracted_text = ""
    for out in extract.output:
        if out.type == "message":
            for c in out.content:
                if c.type == "output_text":
                    extracted_text += c.text

    lead_saved = False
    lead_id = None

    try:
        data = json.loads(extracted_text)
        if data.get("intent") == "lead" and data.get("lead") and not data.get("missing_fields"):
            lead_id = save_lead(data["lead"], raw_json=extracted_text)
            lead_saved = True

            body = (
                f"Neuer Lead (ID {lead_id})\n\n"
                f"Name: {data['lead'].get('name')}\n"
                f"Firma: {data['lead'].get('company')}\n"
                f"Branche: {data['lead'].get('industry')}\n"
                f"Ziel: {data['lead'].get('goal')}\n"
                f"Status: {data['lead'].get('status')}\n"
                f"Budget: {data['lead'].get('budget')}\n"
                f"Zeitplan: {data['lead'].get('timeline')}\n"
                f"Kontakt: {data['lead'].get('contact')}\n"
                f"Notizen: {data['lead'].get('notes')}\n"
            )
            try:
                maybe_send_email(
                    subject=f"PP Consulting Lead #{lead_id}",
                    body=body
                )
            except Exception:
                pass
    except Exception:
        pass

    return ChatResponse(reply=reply_text, lead_saved=lead_saved, lead_id=lead_id)
Commit new file
[ Commit message ]
[ Commit new file ]
Add app.py
