from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import ATTR_APP_VERSION, ATTR_DEVICE_MODEL, DOMAIN, SIGNAL_DEVICE_UPDATE, SIGNAL_CONFIG_CHANGED

def device_info(device):
    return DeviceInfo(identifiers={(DOMAIN, device.device_id)}, name=device.name, manufacturer="Android Voice Assistant", model=device.state.get(ATTR_DEVICE_MODEL, "Android"), sw_version=device.state.get(ATTR_APP_VERSION, "unknown"))

from homeassistant.components.text import TextEntity
async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ColorTextEntity(d, 'led_idle_color', 'Farbe: Bereit', '#00C853') for d in coordinator.devices.values()], True)
class ColorTextEntity(TextEntity):
    _attr_has_entity_name = True; _attr_entity_category = 'config'; _attr_icon = 'mdi:palette'; _attr_pattern = r'^#[0-9A-Fa-f]{6}$'
    def __init__(self, device, key, name, default): self._device=device; self._key=key; self._default=default; self._attr_unique_id=f"{device.device_id}_{key}"; self._attr_name=name
    @property
    def native_value(self): return self._device.config.get(self._key, self._default)
    @property
    def available(self): return self._device.is_connected
    @property
    def device_info(self): return device_info(self._device)
    async def async_set_value(self, value: str): self._device.update_config({self._key: value})
