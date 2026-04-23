"""
WhatsApp messaging service — supports Meta Cloud API and Console mode.
"""

from __future__ import annotations

import httpx
from rich.console import Console
from rich.panel import Panel

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()
console = Console()


class WhatsAppService:
    """Abstraction over WhatsApp message sending."""

    def __init__(self):
        self.mode = settings.whatsapp_mode
        self.phone_id = settings.whatsapp_phone_number_id
        self.token = settings.whatsapp_access_token

    async def send_message(self, to: str, text: str) -> bool:
        """Send a text message to a WhatsApp number."""
        if self.mode == "console":
            return self._send_console(to, text)
        elif self.mode == "meta_cloud":
            return await self._send_meta_cloud(to, text)
        return False

    def _send_console(self, to: str, text: str) -> bool:
        """Print message to console (development mode)."""
        console.print(Panel(
            text,
            title=f"📱 WhatsApp → {to}",
            border_style="green",
            padding=(1, 2),
        ))
        return True

    async def _send_meta_cloud(self, to: str, text: str) -> bool:
        """Send via Meta WhatsApp Cloud API."""
        url = f"https://graph.facebook.com/v19.0/{self.phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    logger.info("whatsapp_sent", to=to)
                    return True
                else:
                    logger.error("whatsapp_error", status=resp.status_code, body=resp.text)
                    return False
        except Exception as e:
            logger.error("whatsapp_exception", error=str(e))
            return False

    async def send_template(self, to: str, template_name: str, params: list[str]) -> bool:
        """Send a pre-approved template message (required for initiating conversations)."""
        if self.mode == "console":
            console.print(Panel(
                f"Template: {template_name}\nParams: {params}",
                title=f"📱 Template → {to}",
                border_style="cyan",
            ))
            return True

        url = f"https://graph.facebook.com/v19.0/{self.phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en"},
                "components": [{
                    "type": "body",
                    "parameters": [{"type": "text", "text": p} for p in params],
                }],
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload, headers=headers)
                return resp.status_code == 200
        except Exception as e:
            logger.error("template_error", error=str(e))
            return False


# Singleton
_whatsapp_service = None


def get_whatsapp_service() -> WhatsAppService:
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
