"""
Telegram webhook endpoint — handles incoming messages from Telegram Bot API.
"""

from __future__ import annotations

import traceback
from fastapi import APIRouter, Depends, Request

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.services.orchestrator import OrchestrationService
from app.services.telegram import get_telegram_service
from app.services.telegram_commands import process_telegram_command

router = APIRouter(prefix="/webhook", tags=["Webhook"])
logger = get_logger(__name__)
settings = get_settings()


@router.post("/telegram")
async def receive_message_telegram(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Receive incoming Telegram messages via webhook (POST).
    
    Telegram sends updates as JSON POST requests to this endpoint.
    Production-ready webhook implementation with command support.
    """
    try:
        body = await request.json()
        
        # Verify webhook secret if provided
        secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if settings.telegram_webhook_secret and secret_header != settings.telegram_webhook_secret:
            logger.warning("telegram_signature_invalid")
            return {"status": "forbidden"}

        # Handle message update
        if "message" in body:
            message = body["message"]
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")
            user_id = message.get("from", {}).get("id")

            if not chat_id or not text:
                return {"status": "invalid_message"}

            logger.info(
                "message_received",
                chat_id=chat_id,
                user_id=user_id,
                preview=text[:50],
            )

            telegram = get_telegram_service()
            service = OrchestrationService(db)
            
            # Check for memory commands first
            command_response = await process_telegram_command(str(chat_id), text, db)
            
            if command_response:
                # Memory command was handled
                await telegram.send_message(str(chat_id), command_response)
                response = command_response
            else:
                # Regular orchestration handling
                response = await service.handle_incoming_message(str(chat_id), text)

            return {"status": "processed", "response_preview": response[:100]}

        # Handle callback query (button presses)
        elif "callback_query" in body:
            callback = body["callback_query"]
            chat_id = callback.get("message", {}).get("chat", {}).get("id")
            callback_id = callback.get("id")
            data = callback.get("data", "")

            logger.info(
                "callback_received",
                callback_id=callback_id,
                data=data,
            )

            # Handle button callback
            telegram = get_telegram_service()
            await telegram.answer_callback_query(callback_id)
            service = OrchestrationService(db)
            response = await service.handle_incoming_message(str(chat_id), f"/{data}")

            return {"status": "processed", "callback_id": callback_id}

        else:
            logger.info("update_ignored", update_type=list(body.keys()))
            return {"status": "ignored"}

    except Exception as e:
        logger.error(
            "telegram_webhook_error", 
            error=str(e), 
            trace=traceback.format_exc()
        )
        return {"status": "error", "detail": str(e)[:100]}


@router.post("/console")
async def console_message(request: Request, db: AsyncSession = Depends(get_db)):
    """Development endpoint — simulate messages via API."""
    body = await request.json()
    user_id = body.get("user_id") or body.get("chat_id", "999999")
    message = body.get("message", "")

    if not message:
        return {"error": "message is required"}

    service = OrchestrationService(db)
    response = await service.handle_incoming_message(user_id, message)

    return {
        "status": "ok",
        "user_id": user_id,
        "response": response,
    }
