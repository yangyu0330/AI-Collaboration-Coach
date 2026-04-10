"""Manage Telegram webhook registration.

Usage:
    python -m scripts.set_webhook --set
    python -m scripts.set_webhook --delete
    python -m scripts.set_webhook --info
"""

from __future__ import annotations

import argparse
import sys

import httpx

from apps.api.config import settings


def _api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"


def _request(method: str, payload: dict | None = None) -> dict:
    with httpx.Client(timeout=10.0) as client:
        if payload is None:
            response = client.post(_api_url(method)) if method != "getWebhookInfo" else client.get(
                _api_url(method)
            )
        else:
            response = client.post(_api_url(method), json=payload)

    response.raise_for_status()
    return response.json()


def set_webhook() -> int:
    payload: dict[str, object] = {
        "url": settings.webhook_url,
        "allowed_updates": ["message", "edited_message"],
    }
    if settings.telegram_secret_token:
        payload["secret_token"] = settings.telegram_secret_token

    result = _request("setWebhook", payload)
    if result.get("ok"):
        print(f"Webhook set: {settings.webhook_url}")
        return 0

    print(f"Failed to set webhook: {result}")
    return 1


def delete_webhook() -> int:
    result = _request("deleteWebhook")
    if result.get("ok"):
        print("Webhook deleted")
        return 0

    print(f"Failed to delete webhook: {result}")
    return 1


def get_webhook_info() -> int:
    result = _request("getWebhookInfo")
    if not result.get("ok"):
        print(f"Failed to get webhook info: {result}")
        return 1

    info = result.get("result", {})
    print(f"URL: {info.get('url', '')}")
    print(f"Pending updates: {info.get('pending_update_count', 0)}")
    print(f"Last error message: {info.get('last_error_message', '')}")
    print(f"Allowed updates: {info.get('allowed_updates', [])}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Telegram webhook manager")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--set", action="store_true", help="Set webhook")
    group.add_argument("--delete", action="store_true", help="Delete webhook")
    group.add_argument("--info", action="store_true", help="Show webhook info")
    args = parser.parse_args()

    if not settings.telegram_bot_token:
        print("TELEGRAM_BOT_TOKEN is missing in .env")
        return 1

    try:
        if args.set:
            if not settings.webhook_url:
                print("WEBHOOK_URL is missing in .env")
                return 1
            return set_webhook()
        if args.delete:
            return delete_webhook()
        return get_webhook_info()
    except httpx.HTTPError as exc:
        print(f"Telegram API request failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

