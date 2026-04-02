from __future__ import annotations

import logging

from aiohttp import web
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.http import HomeAssistantView

from .connection import ConnectionManager, DeviceConnection
from .const import CONF_API_KEY, CONF_DEVICE_ID, CONF_DEVICE_NAME, DOMAIN, REGISTER_PATH, WS_PATH

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["assist_satellite", "binary_sensor", "button", "media_player", "select", "sensor", "switch"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    if "manager" not in hass.data[DOMAIN]:
        manager = ConnectionManager(hass)
        hass.data[DOMAIN]["manager"] = manager
        hass.http.register_view(AndroidVoiceSatelliteWSView(manager))
        hass.http.register_view(AndroidVoiceSatelliteRegisterView(manager, hass))
        _LOGGER.info("Registered Android Voice Satellite endpoints on %s and %s", WS_PATH, REGISTER_PATH)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    manager: ConnectionManager = hass.data[DOMAIN]["manager"]
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
        data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if data:
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
        return self.json(
            {
                "status": "pending",
                "device_id": pending.device_id,
                "device_name": pending.device_name,
                "api_key": pending.api_key,
                "ws_url": f"{base}{WS_PATH}",
            }
        )
