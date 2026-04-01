from __future__ import annotations
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, PHASE_NAMES
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]["connection"]
    async_add_entities([VoicePhaseSensor(c), BatterySensor(c)])
class _Base(SensorEntity):
    _attr_has_entity_name = True
    def __init__(self, c): self._conn = c; self._attr_device_info = {"identifiers": {(DOMAIN, c.device_id)}}
class VoicePhaseSensor(_Base):
    _attr_name = "Voice Assistant Phase"; _attr_icon = "mdi:account-voice"
    def __init__(self, c): super().__init__(c); self._attr_unique_id = f"{c.device_id}_voice_phase"
    @property
    def native_value(self): return PHASE_NAMES.get(self._conn.phase, 'Unknown')
class BatterySensor(_Base):
    _attr_name = "Battery"; _attr_icon = "mdi:battery"; _attr_native_unit_of_measurement = "%"; _attr_device_class = "battery"
    def __init__(self, c): super().__init__(c); self._attr_unique_id = f"{c.device_id}_battery"
    @property
    def native_value(self): return self._conn.battery
