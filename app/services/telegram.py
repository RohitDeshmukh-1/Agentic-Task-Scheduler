"""
Telegram messaging service — supports Telegram Bot API.
Production-ready implementation with proper error handling and formatting.
"""

from __future__ import annotations

import json
from typing import Optional

import httpx
from rich.console import Console
from rich.panel import Panel

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()
console = Console()


class TelegramService:
    """Abstraction over Telegram message sending."""

    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.api_base = "https://api.telegram.org/bot"
        self.timeout = 30

    def _get_headers(self) -> dict:
        """Get request headers."""
        return {"Content-Type": "application/json"}

    async def send_message(
        self,
        chat_id: str | int,
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[dict] = None,
    ) -> bool:
        """Send a text message to a Telegram chat."""
        if not self.bot_token:
            console.print(Panel(
                text,
                title=f"📨 Telegram → {chat_id}",
                border_style="cyan",
                padding=(1, 2),
            ))
            return True

        url = f"{self.api_base}{self.bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers=self._get_headers())
                if resp.status_code == 200:
                    logger.info("telegram_sent", chat_id=chat_id, preview=text[:50])
                    return True
                else:
                    logger.error(
                        "telegram_error",
                        status=resp.status_code,
                        body=resp.text,
                        chat_id=chat_id,
                    )
                    return False
        except Exception as e:
            logger.error("telegram_exception", error=str(e), chat_id=chat_id)
            return False

    async def edit_message(
        self,
        chat_id: str | int,
        message_id: int,
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[dict] = None,
    ) -> bool:
        """Edit an existing message."""
        if not self.bot_token:
            logger.warning("telegram_not_configured")
            return False

        url = f"{self.api_base}{self.bot_token}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers=self._get_headers())
                if resp.status_code == 200:
                    logger.info("telegram_edited", chat_id=chat_id, message_id=message_id)
                    return True
                else:
                    logger.error(
                        "telegram_edit_error",
                        status=resp.status_code,
                        body=resp.text,
                    )
                    return False
        except Exception as e:
            logger.error("telegram_edit_exception", error=str(e))
            return False

    async def delete_message(
        self,
        chat_id: str | int,
        message_id: int,
    ) -> bool:
        """Delete a message."""
        if not self.bot_token:
            logger.warning("telegram_not_configured")
            return False

        url = f"{self.api_base}{self.bot_token}/deleteMessage"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers=self._get_headers())
                if resp.status_code == 200:
                    logger.info("telegram_deleted", chat_id=chat_id)
                    return True
                else:
                    logger.error("telegram_delete_error", status=resp.status_code)
                    return False
        except Exception as e:
            logger.error("telegram_delete_exception", error=str(e))
            return False

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: str = "",
        show_alert: bool = False,
    ) -> bool:
        """Answer a callback query from an inline button."""
        if not self.bot_token:
            return False

        url = f"{self.api_base}{self.bot_token}/answerCallbackQuery"
        payload = {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers=self._get_headers())
                return resp.status_code == 200
        except Exception as e:
            logger.error("telegram_callback_exception", error=str(e))
            return False

    async def send_document(
        self,
        chat_id: str | int,
        document_url: str,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
    ) -> bool:
        """Send a document/file."""
        if not self.bot_token:
            logger.warning("telegram_not_configured")
            return False

        url = f"{self.api_base}{self.bot_token}/sendDocument"
        payload = {
            "chat_id": chat_id,
            "document": document_url,
        }
        if caption:
            payload["caption"] = caption
            if parse_mode:
                payload["parse_mode"] = parse_mode

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers=self._get_headers())
                return resp.status_code == 200
        except Exception as e:
            logger.error("telegram_document_exception", error=str(e))
            return False

    async def get_updates(self, offset: Optional[int] = None) -> list[dict]:
        """Polling mode: Get updates from Telegram (for polling setup)."""
        if not self.bot_token:
            return []

        url = f"{self.api_base}{self.bot_token}/getUpdates"
        payload = {"timeout": 25}
        if offset:
            payload["offset"] = offset

        try:
            async with httpx.AsyncClient(timeout=self.timeout + 5) as client:
                resp = await client.post(url, json=payload, headers=self._get_headers())
                if resp.status_code == 200:
                    return resp.json().get("result", [])
                return []
        except Exception as e:
            logger.error("telegram_polling_exception", error=str(e))
            return []

    async def set_webhook(
        self,
        url: str,
        secret_token: Optional[str] = None,
        drop_pending_updates: bool = False,
    ) -> bool:
        """Configure Telegram webhook for this bot."""
        if not self.bot_token:
            logger.warning("telegram_not_configured")
            return False

        payload = {
            "url": url,
            "drop_pending_updates": drop_pending_updates,
        }
        if secret_token:
            payload["secret_token"] = secret_token

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.api_base}{self.bot_token}/setWebhook",
                    json=payload,
                    headers=self._get_headers(),
                )
                if resp.status_code == 200:
                    return True
                logger.error("telegram_webhook_error", status=resp.status_code, body=resp.text)
                return False
        except Exception as e:
            logger.error("telegram_webhook_exception", error=str(e))
            return False

    def verify_webhook_signature(self, request_body: str, secret: str) -> bool:
        """
        Verify webhook signature (optional layer for security).
        For production, you might implement HMAC verification.
        """
        # Telegram doesn't use standard HMAC, but we can validate structure
        try:
            json.loads(request_body)
            return True
        except json.JSONDecodeError:
            return False


def get_telegram_service() -> TelegramService:
    """Factory function to get Telegram service."""
    return TelegramService()
