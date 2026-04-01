from __future__ import annotations
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]["connection"]
    async_add_entities([RestartButton(c), FactoryResetButton(c)])
class RestartButton(ButtonEntity):
    _attr_has_entity_name = True; _attr_name = "Restart"; _attr_icon = "mdi:restart"; _attr_entity_category = "config"
    def __init__(self, c): self._conn = c; self._attr_unique_id = f"{c.device_id}_restart"; self._attr_device_info = {"identifiers": {(DOMAIN, c.device_id)}}
    async def async_press(self): await self._conn.cmd_restart()
class FactoryResetButton(ButtonEntity):
    _attr_has_entity_name = True; _attr_name = "Factory Reset"; _attr_icon = "mdi:restart-alert"; _attr_entity_category = "diagnostic"
    def __init__(self, c): self._conn = c; self._attr_unique_id = f"{c.device_id}_factory_reset"; self._attr_device_info = {"identifiers": {(DOMAIN, c.device_id)}}
    async def async_press(self): await self._conn.cmd_factory_reset()
