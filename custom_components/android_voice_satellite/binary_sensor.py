from __future__ import annotations
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([ConnectionBinarySensor(hass.data[DOMAIN][entry.entry_id]["connection"])])
class ConnectionBinarySensor(BinarySensorEntity):
    _attr_has_entity_name = True; _attr_name = "Connected"; _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    def __init__(self, c): self._conn = c; self._attr_unique_id = f"{c.device_id}_connected"; self._attr_device_info = {"identifiers": {(DOMAIN, c.device_id)}}
    @property
    def is_on(self): return self._conn.is_connected
