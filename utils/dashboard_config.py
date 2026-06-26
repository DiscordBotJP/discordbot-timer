import asyncio
import base64
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from constants import DASHBOARD_CONFIG_SECRET, DASHBOARD_CONFIG_URL, TOKEN


@dataclass(frozen=True)
class GuildDashboardSetting:
    guild_id: str
    enabled: bool
    interval_minutes: int
    anchor_time: str
    timezone: str


class DashboardSettings:
    def __init__(self, payload: dict[str, Any] | None) -> None:
        self.payload = payload or {}
        self.defaults = self.payload.get('defaults') or {}
        self.settings = {
            str(setting.get('guildId')): setting
            for setting in self.payload.get('settings', [])
            if setting.get('guildId')
        }

    def for_guild(self, guild_id: int | str) -> GuildDashboardSetting:
        raw = {
            **self.defaults,
            **self.settings.get(str(guild_id), {}),
        }
        return GuildDashboardSetting(
            guild_id=str(guild_id),
            enabled=raw.get('enabled') is not False,
            interval_minutes=int(raw.get('intervalMinutes') or 0),
            anchor_time=str(raw.get('anchorTime') or '00:00'),
            timezone=str(raw.get('timezone') or 'Asia/Tokyo'),
        )


class DashboardConfigCache:
    def __init__(self, ttl_seconds: int = 60) -> None:
        self.ttl_seconds = ttl_seconds
        self._settings = DashboardSettings(None)
        self._expires_at = 0.0

    async def get(self) -> DashboardSettings:
        now = time.monotonic()
        if now < self._expires_at:
            return self._settings
        self._settings = await fetch_dashboard_settings()
        self._expires_at = now + self.ttl_seconds
        return self._settings


def bot_id_from_token() -> str:
    token_head = (TOKEN or '').split('.', 1)[0]
    padding = '=' * (-len(token_head) % 4)
    return base64.urlsafe_b64decode(f'{token_head}{padding}').decode()


async def fetch_dashboard_settings() -> DashboardSettings:
    if not TOKEN or not DASHBOARD_CONFIG_SECRET:
        return DashboardSettings(None)

    bot_id = bot_id_from_token()
    base_url = DASHBOARD_CONFIG_URL.rstrip('/')
    url = f'{base_url}/{bot_id}'
    parsed = urlparse(url)
    path = parsed.path
    timestamp = str(int(time.time() * 1000))
    signature = _sign(f'{timestamp}.GET.{path}', DASHBOARD_CONFIG_SECRET)

    def request_settings() -> dict[str, Any] | None:
        request = urllib.request.Request(
            url,
            headers={
                'Accept': 'application/json',
                'X-Dashboard-Timestamp': timestamp,
                'X-Dashboard-Signature': f'v1={signature}',
            },
            method='GET',
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return json.loads(response.read().decode())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return None

    return DashboardSettings(await asyncio.to_thread(request_settings))


def _sign(value: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), value.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip('=')
