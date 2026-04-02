from __future__ import annotations

import html
import io
import logging

from .vendor import qrcode
from .vendor.qrcode.image import svg as qrcode_svg
from aiohttp import web
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.http import HomeAssistantView

from .connection import ConnectionManager, DeviceConnection, ensure_manager
from .const import CONF_API_KEY, CONF_DEVICE_ID, CONF_DEVICE_NAME, DOMAIN, PAIR_PATH, PAIRING_PAGE_PATH, REGISTER_PATH, WS_PATH

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["assist_satellite", "binary_sensor", "button", "media_player", "select", "sensor", "switch"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    await ensure_manager(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    manager = await ensure_manager(hass)
    conn = DeviceConnection(
        hass=hass,
        entry=entry,
        device_id=entry.data[CONF_DEVICE_ID],
        api_key=entry.data[CONF_API_KEY],
        device_name=entry.data[CONF_DEVICE_NAME],
    )
    manager.register_device(conn.device_id, conn.api_key, conn)
    hass.data[DOMAIN][entry.entry_id] = {"connection": conn}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if data and "manager" in hass.data.get(DOMAIN, {}):
            hass.data[DOMAIN]["manager"].unregister_device(data["connection"].device_id)
    return ok


class AndroidVoiceSatelliteWSView(HomeAssistantView):
    url = WS_PATH
    name = "api:android_voice_satellite:ws"
    requires_auth = False
    cors_allowed = True

    def __init__(self, manager: ConnectionManager) -> None:
        self._manager = manager

    async def get(self, request: web.Request) -> web.StreamResponse:
        ws = web.WebSocketResponse(heartbeat=30, max_msg_size=4 * 1024 * 1024)
        await ws.prepare(request)
        await self._manager.handle_connection(ws)
        return ws


class AndroidVoiceSatelliteRegisterView(HomeAssistantView):
    url = REGISTER_PATH
    name = "api:android_voice_satellite:register"
    requires_auth = True
    cors_allowed = True

    def __init__(self, manager: ConnectionManager, hass: HomeAssistant) -> None:
        self._manager = manager
        self._hass = hass

    async def post(self, request: web.Request) -> web.Response:
        payload = await request.json()
        client_id = str(payload.get("client_id", "")).strip()
        device_name = str(payload.get("device_name", "")).strip() or "Android Satellite"
        if not client_id:
            return self.json({"error": "missing_client_id"}, status_code=400)
        pending = self._manager.create_or_update_pending(
            client_id=client_id,
            device_name=device_name,
            app_version=payload.get("app_version"),
            device_model=payload.get("device_model"),
            android_version=payload.get("android_version"),
        )
        base = self._hass.config.external_url or self._hass.config.internal_url or "http://homeassistant.local:8123"
        return self.json({"status": "pending", "device_id": pending.device_id, "device_name": pending.device_name, "api_key": pending.api_key, "ws_url": f"{base}{WS_PATH}"})


class AndroidVoiceSatellitePairView(HomeAssistantView):
    url = PAIR_PATH
    name = "api:android_voice_satellite:pair"
    requires_auth = False
    cors_allowed = True

    def __init__(self, manager: ConnectionManager, hass: HomeAssistant) -> None:
        self._manager = manager
        self._hass = hass

    async def post(self, request: web.Request) -> web.Response:
        payload = await request.json()
        pair_token = str(payload.get("pair_token", "")).strip()
        client_id = str(payload.get("client_id", "")).strip()
        device_name = str(payload.get("device_name", "")).strip() or "Android Satellite"
        if not pair_token or not client_id:
            return self.json({"error": "missing_fields"}, status_code=400)
        session = self._manager.get_pairing_session(pair_token)
        if session is None:
            return self.json({"error": "invalid_or_expired_pair_token"}, status_code=410)
        pending = self._manager.create_or_update_pending(
            client_id=client_id,
            device_name=device_name,
            app_version=payload.get("app_version"),
            device_model=payload.get("device_model"),
            android_version=payload.get("android_version"),
            pair_token=pair_token,
        )
        base = self._hass.config.external_url or self._hass.config.internal_url or "http://homeassistant.local:8123"
        return self.json({"status": "paired", "device_id": pending.device_id, "device_name": pending.device_name, "api_key": pending.api_key, "ws_url": f"{base}{WS_PATH}"})


class AndroidVoiceSatellitePairingPageView(HomeAssistantView):
    url = PAIRING_PAGE_PATH
    name = "api:android_voice_satellite:pairing_page"
    requires_auth = True
    cors_allowed = True

    def __init__(self, manager: ConnectionManager, hass: HomeAssistant) -> None:
        self._manager = manager
        self._hass = hass

    async def get(self, request: web.Request, pair_token: str) -> web.Response:
        session = self._manager.get_pairing_session(pair_token)
        if session is None:
            return web.Response(status=404, text="Pairing code expired")
        base = self._hass.config.external_url or self._hass.config.internal_url or "http://homeassistant.local:8123"
        payload = self._manager.get_pairing_payload(base, pair_token)
        qr = qrcode.QRCode(border=2, box_size=8)
        qr.add_data(payload)
        qr.make(fit=True)
        image = qr.make_image(image_factory=qrcode_svg.SvgImage)
        svg_buffer = io.BytesIO()
        image.save(svg_buffer)
        qr_svg = svg_buffer.getvalue().decode("utf-8")
        html_body = f"""<!doctype html><html><head><meta charset='utf-8'><title>Android Voice Satellite Pairing</title></head>
<body style='font-family:sans-serif;text-align:center;padding:24px'>
<h2>Android Voice Satellite Pairing</h2>
<p>Scanne diesen QR-Code in der Android-App.</p>
<div style='display:inline-block;background:#fff;padding:16px;border-radius:12px'>{qr_svg}</div>
<p>Fallback-Payload:</p><pre style='white-space:pre-wrap;word-break:break-all'>{html.escape(payload)}</pre>
<p>Dieser Pairing-Code läuft in wenigen Minuten ab.</p>
</body></html>"""
        return web.Response(text=html_body, content_type="text/html")
