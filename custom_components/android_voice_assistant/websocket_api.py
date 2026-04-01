"""WebSocket API for Android Voice Assistant."""
from __future__ import annotations
import voluptuous as vol
from typing import Any
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from .const import *
_REGISTERED = False
@callback
def async_register_websocket_api(hass: HomeAssistant) -> None:
    global _REGISTERED
    if _REGISTERED: return
    _REGISTERED = True
    websocket_api.async_register_command(hass, ws_register_device)
    websocket_api.async_register_command(hass, ws_update_state)
    websocket_api.async_register_command(hass, ws_get_config)
    websocket_api.async_register_command(hass, ws_set_config)
    websocket_api.async_register_command(hass, ws_list_devices)
def _get_coordinator(hass: HomeAssistant):
    for entry_data in hass.data.get(DOMAIN, {}).values(): return entry_data
    return None
@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_REGISTER, vol.Required(CONF_DEVICE_ID): str, vol.Required(CONF_DEVICE_NAME): str})
@websocket_api.async_response
async def ws_register_device(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    c = _get_coordinator(hass)
    if c is None: connection.send_error(msg["id"], "not_ready", "Integration not loaded"); return
    d = c.register_device(msg[CONF_DEVICE_ID], msg[CONF_DEVICE_NAME], {})
    await c.async_save()
    connection.send_result(msg["id"], {"success": True, "device_id": d.device_id, "config": d.config})
@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_UPDATE_STATE, vol.Required(CONF_DEVICE_ID): str})
@websocket_api.async_response
async def ws_update_state(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    c = _get_coordinator(hass)
    d = c.get_device(msg[CONF_DEVICE_ID]) if c else None
    if d is None: connection.send_error(msg["id"], "not_found", "device not registered"); return
    d.update_state({k: v for k, v in msg.items() if k not in ("type", "id", CONF_DEVICE_ID)})
    connection.send_result(msg["id"], {"success": True})
@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_GET_CONFIG, vol.Required(CONF_DEVICE_ID): str})
@websocket_api.async_response
async def ws_get_config(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    c = _get_coordinator(hass); d = c.get_device(msg[CONF_DEVICE_ID]) if c else None
    if d is None: connection.send_error(msg["id"], "not_found", "device not registered"); return
    connection.send_result(msg["id"], {"device_id": d.device_id, "config": d.config, "state": d.state})
@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_SET_CONFIG, vol.Required(CONF_DEVICE_ID): str, vol.Required("config"): dict})
@websocket_api.async_response
async def ws_set_config(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    c = _get_coordinator(hass); d = c.get_device(msg[CONF_DEVICE_ID]) if c else None
    if d is None: connection.send_error(msg["id"], "not_found", "device not registered"); return
    d.update_config(msg["config"]); await c.async_save(); connection.send_result(msg["id"], {"success": True, "config": d.config})
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/list_devices"})
@websocket_api.async_response
async def ws_list_devices(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    c = _get_coordinator(hass)
    devices = [] if c is None else [{"device_id": d.device_id, "name": d.name, "connected": d.is_connected, "phase": d.state.get(ATTR_PHASE), "battery": d.state.get(ATTR_BATTERY_LEVEL), "volume": d.state.get(ATTR_VOLUME)} for d in c.devices.values()]
    connection.send_result(msg["id"], {"devices": devices})
