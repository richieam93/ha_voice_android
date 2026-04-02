from __future__ import annotations

import asyncio
import json
import logging
import secrets
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from aiohttp import web, WSMsgType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    CONF_CLIENT_ID,
    DOMAIN,
    PAIRING_TTL_SECONDS,
    PHASE_IDLE,
    PHASE_MUTED,
    PHASE_NOT_READY,
    SIGNAL_DEVICE_CONNECTED,
    SIGNAL_DEVICE_DISCONNECTED,
    SIGNAL_DEVICE_STATE,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class PendingRegistration:
    client_id: str
    device_id: str
    api_key: str
    device_name: str
    app_version: str | None = None
    device_model: str | None = None
    android_version: str | None = None
    pair_token: str | None = None


@dataclass
class PairingSession:
    pair_token: str
    created_at: float
    expires_at: float

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class DeviceConnection:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, device_id: str, api_key: str, device_name: str) -> None:
        self.hass = hass
        self.entry = entry
        self.device_id = device_id
        self.api_key = api_key
        self.device_name = device_name
        self.client_id = entry.data.get(CONF_CLIENT_ID)
        self._ws: web.WebSocketResponse | None = None
        self.audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self.announcement_done_event = asyncio.Event()
        self.connected = False
        self.phase = PHASE_NOT_READY
        self.volume = 0.7
        self.muted = False
        self.battery: int | None = None
        self.voice_enabled = True
        self.button_sounds = True
        self.wake_sound = True
        self.timer_ringing = False
        self.alarm_action = "Play sound"
        self.vad_sensitivity = "Aggressive"
        self.active_wake_word_ids = ["okay_nabu"]
        self.app_version: str | None = None
        self.device_model: str | None = None
        self.android_version: str | None = None

    @property
    def is_connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    async def send_json(self, data: dict[str, Any]) -> None:
        if not self._ws or self._ws.closed:
            return
        await self._ws.send_json(data)

    async def send_bytes(self, data: bytes) -> None:
        if not self._ws or self._ws.closed:
            return
        await self._ws.send_bytes(data)

    async def cmd_start_mic(self) -> None:
        await self.send_json({"type": "start_mic"})

    async def cmd_stop_mic(self) -> None:
        await self.send_json({"type": "stop_mic"})
        await self.audio_queue.put(None)

    async def cmd_play_url(self, url: str, announcement: bool = False) -> None:
        self.announcement_done_event.clear()
        await self.send_json({"type": "play_url", "url": url, "announcement": announcement})

    async def cmd_stop_playback(self, announcement: bool = False) -> None:
        await self.send_json({"type": "stop_playback", "announcement": announcement})

    async def cmd_set_volume(self, volume: float) -> None:
        self.volume = volume
        await self.send_json({"type": "set_volume", "volume": volume})
        self._dispatch_state()

    async def cmd_set_config(self, config: dict[str, Any]) -> None:
        await self.send_json({"type": "set_config", "config": config})

    async def cmd_restart(self) -> None:
        await self.send_json({"type": "restart"})

    async def cmd_factory_reset(self) -> None:
        await self.send_json({"type": "factory_reset"})

    async def cmd_pipeline_event(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        await self.send_json({"type": "pipeline_event", "event_type": event_type, "data": data or {}})

    def set_ws(self, ws: web.WebSocketResponse | None) -> None:
        self._ws = ws
        self.connected = ws is not None and not ws.closed
        self.phase = PHASE_IDLE if self.connected and self.voice_enabled else (PHASE_MUTED if self.connected else PHASE_NOT_READY)
        self._dispatch_state()

    def set_phase(self, phase: int) -> None:
        self.phase = phase
        self._dispatch_state()

    @callback
    def _dispatch_state(self) -> None:
        async_dispatcher_send(self.hass, f"{SIGNAL_DEVICE_STATE}_{self.device_id}")

    async def audio_stream(self):
        while not self.audio_queue.empty():
            self.audio_queue.get_nowait()
        while True:
            chunk = await self.audio_queue.get()
            if chunk is None:
                return
            yield chunk


async def ensure_manager(hass: HomeAssistant) -> "ConnectionManager":
    hass.data.setdefault(DOMAIN, {})
    manager = hass.data[DOMAIN].get("manager")
    if manager is None:
        manager = ConnectionManager(hass)
        hass.data[DOMAIN]["manager"] = manager
        from .__init__ import AndroidVoiceSatellitePairView, AndroidVoiceSatellitePairingPageView, AndroidVoiceSatelliteRegisterView, AndroidVoiceSatelliteWSView
        hass.http.register_view(AndroidVoiceSatelliteWSView(manager))
        hass.http.register_view(AndroidVoiceSatelliteRegisterView(manager, hass))
        hass.http.register_view(AndroidVoiceSatellitePairView(manager, hass))
        hass.http.register_view(AndroidVoiceSatellitePairingPageView(manager, hass))
    return manager


class ConnectionManager:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._devices: dict[str, DeviceConnection] = {}
        self._keys: dict[str, str] = {}
        self._pending: dict[str, PendingRegistration] = {}
        self._pairs: dict[str, PairingSession] = {}

    def _cleanup(self) -> None:
        now = time.time()
        self._pairs = {k: v for k, v in self._pairs.items() if v.expires_at > now}
        self._pending = {k: v for k, v in self._pending.items() if not v.pair_token or v.pair_token in self._pairs}

    def register_device(self, device_id: str, api_key: str, connection: DeviceConnection) -> None:
        self._devices[device_id] = connection
        self._keys[api_key] = device_id

    def unregister_device(self, device_id: str) -> None:
        conn = self._devices.pop(device_id, None)
        if conn:
            self._keys.pop(conn.api_key, None)

    def create_pairing_session(self) -> PairingSession:
        self._cleanup()
        token = secrets.token_urlsafe(24)
        session = PairingSession(pair_token=token, created_at=time.time(), expires_at=time.time() + PAIRING_TTL_SECONDS)
        self._pairs[token] = session
        return session

    def get_pairing_session(self, pair_token: str) -> PairingSession | None:
        self._cleanup()
        return self._pairs.get(pair_token)

    def get_pending_devices(self, pair_token: str | None = None) -> list[PendingRegistration]:
        self._cleanup()
        values = list(self._pending.values())
        if pair_token:
            values = [item for item in values if item.pair_token == pair_token]
        return sorted(values, key=lambda item: item.device_name.lower())

    def create_or_update_pending(self, *, client_id: str, device_name: str, app_version: str | None, device_model: str | None, android_version: str | None, pair_token: str | None = None) -> PendingRegistration:
        existing = self._pending.get(client_id)
        if existing is None:
            existing = PendingRegistration(
                client_id=client_id,
                device_id=uuid.uuid4().hex[:12],
                api_key=secrets.token_hex(32),
                device_name=device_name,
                app_version=app_version,
                device_model=device_model,
                android_version=android_version,
                pair_token=pair_token,
            )
            self._pending[client_id] = existing
        else:
            existing.device_name = device_name
            existing.app_version = app_version
            existing.device_model = device_model
            existing.android_version = android_version
            if pair_token:
                existing.pair_token = pair_token
        return existing

    def pop_pending(self, client_id: str) -> PendingRegistration | None:
        return self._pending.pop(client_id, None)

    def get_pairing_payload(self, base_url: str, pair_token: str) -> str:
        return json.dumps({
            "type": "android_voice_satellite_pair",
            "base_url": base_url,
            "pair_token": pair_token,
        }, separators=(",", ":"))

    def get_pairing_page_url(self, base_url: str, pair_token: str) -> str:
        return f"{base_url}/api/android_voice_satellite/pairing_page/{quote(pair_token, safe='')}"

    async def handle_connection(self, ws: web.WebSocketResponse) -> None:
        conn: DeviceConnection | None = None
        try:
            auth = await asyncio.wait_for(ws.receive_json(), timeout=10)
            if auth.get("type") != "auth":
                await ws.send_json({"type": "auth_failed", "reason": "Expected auth"})
                return
            api_key = auth.get("api_key", "")
            device_id = self._keys.get(api_key)
            if not device_id or device_id not in self._devices:
                await ws.send_json({"type": "auth_failed", "reason": "Invalid API key"})
                return
            conn = self._devices[device_id]
            conn.app_version = auth.get("app_version")
            conn.device_model = auth.get("device_model")
            conn.android_version = auth.get("android_version")
            conn.set_ws(ws)
            await ws.send_json({"type": "auth_ok", "device_name": conn.device_name, "config": self._build_config(conn)})
            async_dispatcher_send(self.hass, f"{SIGNAL_DEVICE_CONNECTED}_{conn.device_id}")

            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                    except json.JSONDecodeError:
                        continue
                    await self._handle_text_message(conn, data)
                elif msg.type == WSMsgType.BINARY:
                    await conn.audio_queue.put(msg.data)
                elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                    break
        finally:
            if conn is not None:
                conn.set_ws(None)
                await conn.audio_queue.put(None)
                async_dispatcher_send(self.hass, f"{SIGNAL_DEVICE_DISCONNECTED}_{conn.device_id}")

    async def _handle_text_message(self, conn: DeviceConnection, data: dict[str, Any]) -> None:
        msg_type = data.get("type", "")
        if msg_type == "wake_word_detected":
            async_dispatcher_send(self.hass, f"{DOMAIN}_wake_word_{conn.device_id}", data.get("wake_word_id", ""), data.get("wake_word_phrase", ""))
        elif msg_type == "state":
            if "volume" in data:
                conn.volume = float(data["volume"])
            if "muted" in data:
                conn.muted = bool(data["muted"])
            if "battery" in data:
                conn.battery = int(data["battery"])
            conn._dispatch_state()
        elif msg_type in ("announcement_done", "tts_done"):
            conn.announcement_done_event.set()
        elif msg_type == "mic_closed":
            await conn.audio_queue.put(None)
        elif msg_type == "event":
            self.hass.bus.async_fire(f"{DOMAIN}_{data.get('name', 'event')}", {"device_id": conn.device_id, **data.get("data", {})})

    @staticmethod
    def _build_config(conn: DeviceConnection) -> dict[str, Any]:
        return {
            "voice_enabled": conn.voice_enabled,
            "button_sounds": conn.button_sounds,
            "wake_sound": conn.wake_sound,
            "alarm_action": conn.alarm_action,
            "vad_sensitivity": conn.vad_sensitivity,
            "active_wake_word_ids": conn.active_wake_word_ids,
            "volume": conn.volume,
        }
