from __future__ import annotations

import logging
from aiohttp import web
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .connection import ConnectionManager, DeviceConnection
from .const import DOMAIN, WS_PATH, CONF_DEVICE_ID, CONF_API_KEY, CONF_DEVICE_NAME

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["assist_satellite", "binary_sensor", "button", "media_player", "select", "sensor", "switch"]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    if "manager" not in hass.data[DOMAIN]:
        manager = ConnectionManager(hass)
        hass.data[DOMAIN]["manager"] = manager
        hass.http.register_view(AndroidVoiceSatelliteWSView(manager))
        _LOGGER.info("Registered Android Voice Satellite endpoint on %s", WS_PATH)
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

class AndroidVoiceSatelliteWSView(web.View):
    url = WS_PATH
    name = "api:android_voice_satellite:ws"
    requires_auth = False
    cors_allowed = True

    def __init__(self, manager: ConnectionManager) -> None:
        self._manager = manager

    async def get(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse(heartbeat=30, max_msg_size=4 * 1024 * 1024)
        await ws.prepare(request)
        await self._manager.handle_connection(ws)
        return ws
