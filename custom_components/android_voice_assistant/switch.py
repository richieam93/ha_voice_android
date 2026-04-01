from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import ATTR_APP_VERSION, ATTR_DEVICE_MODEL, DOMAIN, SIGNAL_DEVICE_UPDATE, SIGNAL_CONFIG_CHANGED

def device_info(device):
    return DeviceInfo(identifiers={(DOMAIN, device.device_id)}, name=device.name, manufacturer="Android Voice Assistant", model=device.state.get(ATTR_DEVICE_MODEL, "Android"), sw_version=device.state.get(ATTR_APP_VERSION, "unknown"))

from homeassistant.components.switch import SwitchEntity
async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ConfigSwitch(d, 'voice_enabled', 'Sprachassistent aktiv') for d in coordinator.devices.values()], True)
class ConfigSwitch(SwitchEntity):
    _attr_has_entity_name = True
    def __init__(self, device, key, name): self._device=device; self._key=key; self._attr_unique_id=f"{device.device_id}_{key}"; self._attr_name=name
    @property
    def is_on(self): return bool(self._device.config.get(self._key, False))
    @property
    def available(self): return self._device.is_connected
    @property
    def device_info(self): return device_info(self._device)
    async def async_turn_on(self, **kwargs): self._device.update_config({self._key: True})
    async def async_turn_off(self, **kwargs): self._device.update_config({self._key: False})
    async def async_added_to_hass(self): self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_DEVICE_UPDATE.format(device_id=self._device.device_id), self.async_write_ha_state))
