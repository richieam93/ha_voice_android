from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import ATTR_APP_VERSION, ATTR_DEVICE_MODEL, DOMAIN, SIGNAL_DEVICE_UPDATE, SIGNAL_CONFIG_CHANGED

def device_info(device):
    return DeviceInfo(identifiers={(DOMAIN, device.device_id)}, name=device.name, manufacturer="Android Voice Assistant", model=device.state.get(ATTR_DEVICE_MODEL, "Android"), sw_version=device.state.get(ATTR_APP_VERSION, "unknown"))

from homeassistant.components.sensor import SensorEntity
async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GenericSensor(d, 'voice_phase', 'Sprachassistent-Phase', 'phase_name') for d in coordinator.devices.values()], True)
class GenericSensor(SensorEntity):
    _attr_has_entity_name = True
    def __init__(self, device, uid, name, key): self._device=device; self._attr_unique_id=f"{device.device_id}_{uid}"; self._attr_name=name; self._key=key
    @property
    def native_value(self): return self._device.state.get(self._key)
    @property
    def available(self): return self._device.is_connected
    @property
    def device_info(self): return device_info(self._device)
    async def async_added_to_hass(self): self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_DEVICE_UPDATE.format(device_id=self._device.device_id), self.async_write_ha_state))
