from __future__ import annotations
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .connection import DeviceConnection
from .const import DOMAIN, ALARM_ACTIONS, WAKE_WORDS, VAD_SENSITIVITIES
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]["connection"]
    async_add_entities([AlarmActionSelect(c), WakeWord1Select(c), WakeWord2Select(c), VadSensitivitySelect(c)])
class _Base(SelectEntity):
    _attr_has_entity_name = True
    def __init__(self, c): self._conn = c; self._attr_device_info = {"identifiers": {(DOMAIN, c.device_id)}}
class AlarmActionSelect(_Base):
    _attr_name = "Alarm action"; _attr_options = ALARM_ACTIONS; _attr_icon = "mdi:bell-plus"
    def __init__(self, c): super().__init__(c); self._attr_unique_id = f"{c.device_id}_alarm_action"
    @property
    def current_option(self): return self._conn.alarm_action
    async def async_select_option(self, option): self._conn.alarm_action = option; await self._conn.cmd_set_config({"alarm_action": option})
class WakeWord1Select(_Base):
    _attr_name = "Wake Word"; _attr_entity_category = "config"; _attr_icon = "mdi:microphone-message"
    def __init__(self, c): super().__init__(c); self._attr_unique_id = f"{c.device_id}_wake_word_1"; self._attr_options = [w['name'] for w in WAKE_WORDS]
    @property
    def current_option(self):
        current = self._conn.active_wake_word_ids[0] if self._conn.active_wake_word_ids else 'okay_nabu'
        return next((w['name'] for w in WAKE_WORDS if w['id'] == current), 'Okay Nabu')
    async def async_select_option(self, option):
        found = next((w['id'] for w in WAKE_WORDS if w['name'] == option), 'okay_nabu')
        self._conn.active_wake_word_ids = [found] + self._conn.active_wake_word_ids[1:]
        await self._conn.cmd_set_config({"active_wake_word_ids": self._conn.active_wake_word_ids})
class WakeWord2Select(_Base):
    _attr_name = "Wake Word 2"; _attr_entity_category = "config"; _attr_icon = "mdi:microphone-message"
    def __init__(self, c): super().__init__(c); self._attr_unique_id = f"{c.device_id}_wake_word_2"; self._none='No wake word'; self._attr_options = [self._none] + [w['name'] for w in WAKE_WORDS]
    @property
    def current_option(self):
        if len(self._conn.active_wake_word_ids) < 2: return self._none
        return next((w['name'] for w in WAKE_WORDS if w['id'] == self._conn.active_wake_word_ids[1]), self._none)
    async def async_select_option(self, option):
        if option == self._none: self._conn.active_wake_word_ids = self._conn.active_wake_word_ids[:1]
        else:
            found = next((w['id'] for w in WAKE_WORDS if w['name'] == option), None)
            if found:
                if len(self._conn.active_wake_word_ids) >= 2: self._conn.active_wake_word_ids[1] = found
                else: self._conn.active_wake_word_ids.append(found)
        await self._conn.cmd_set_config({"active_wake_word_ids": self._conn.active_wake_word_ids})
class VadSensitivitySelect(_Base):
    _attr_name = "Voice Activity Detection"; _attr_entity_category = "config"; _attr_options = VAD_SENSITIVITIES; _attr_icon = "mdi:ear-hearing"
    def __init__(self, c): super().__init__(c); self._attr_unique_id = f"{c.device_id}_vad_sensitivity"
    @property
    def current_option(self): return self._conn.vad_sensitivity
    async def async_select_option(self, option): self._conn.vad_sensitivity = option; await self._conn.cmd_set_config({"vad_sensitivity": option})
