"""
WhatsApp webhook endpoints — handles incoming messages from Meta Cloud API.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, Response

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.services.orchestrator import OrchestrationService

router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhook"])
logger = get_logger(__name__)
settings = get_settings()


@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta Cloud API webhook verification (GET)."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("webhook_verified")
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(content="Forbidden", status_code=403)


@router.post("/whatsapp")
async def receive_message(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive incoming WhatsApp messages (POST)."""
    body = await request.json()

    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "no_messages"}

        msg = messages[0]
        phone = msg.get("from", "")
        text = msg.get("text", {}).get("body", "")

        if not phone or not text:
            return {"status": "invalid_message"}

        logger.info("message_received", phone=phone, preview=text[:50])

        service = OrchestrationService(db)
        response = await service.handle_incoming_message(phone, text)

        return {"status": "processed", "response_preview": response[:100]}

    except Exception as e:
        logger.error("webhook_error", error=str(e))
        return {"status": "error", "detail": str(e)}


@router.post("/console")
async def console_message(request: Request, db: AsyncSession = Depends(get_db)):
    """Development endpoint — simulate WhatsApp messages via API."""
    body = await request.json()
    phone = body.get("phone", "+919999999999")
    message = body.get("message", "")

    if not message:
        return {"error": "message is required"}

    service = OrchestrationService(db)
    response = await service.handle_incoming_message(phone, message)

    return {
        "status": "ok",
        "phone": phone,
        "response": response,
    }
