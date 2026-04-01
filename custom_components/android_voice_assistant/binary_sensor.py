from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import ATTR_APP_VERSION, ATTR_DEVICE_MODEL, DOMAIN, SIGNAL_DEVICE_UPDATE, SIGNAL_CONFIG_CHANGED

def device_info(device):
    return DeviceInfo(identifiers={(DOMAIN, device.device_id)}, name=device.name, manufacturer="Android Voice Assistant", model=device.state.get(ATTR_DEVICE_MODEL, "Android"), sw_version=device.state.get(ATTR_APP_VERSION, "unknown"))

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from .const import ATTR_PHASE, VoicePhase
async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ConnectedSensor(d), ListeningSensor(d) for d in coordinator.devices.values()], True)
class ConnectedSensor(BinarySensorEntity):
    _attr_has_entity_name = True; _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    def __init__(self, device): self._device=device; self._attr_unique_id=f"{device.device_id}_connected"; self._attr_name='Verbunden'
    @property
    def is_on(self): return self._device.is_connected
    @property
    def device_info(self): return device_info(self._device)
class ListeningSensor(BinarySensorEntity):
    _attr_has_entity_name = True
    def __init__(self, device): self._device=device; self._attr_unique_id=f"{device.device_id}_listening"; self._attr_name='Hört zu'; self._attr_icon='mdi:ear-hearing'
    @property
    def is_on(self): return self._device.state.get(ATTR_PHASE) in (VoicePhase.WAITING_FOR_COMMAND, VoicePhase.LISTENING)
    @property
    def device_info(self): return device_info(self._device)
