from __future__ import annotations
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .connection import DeviceConnection
from .const import DOMAIN, SIGNAL_DEVICE_STATE, PHASE_IDLE, PHASE_MUTED
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    c = hass.data[DOMAIN][entry.entry_id]["connection"]
    async_add_entities([VoiceEnabledSwitch(c), ButtonClickSoundsSwitch(c), WakeSoundSwitch(c), TimerRingingSwitch(c)])
class _Base(SwitchEntity):
    _attr_has_entity_name = True
    def __init__(self, c): self._conn = c; self._attr_device_info = {"identifiers": {(DOMAIN, c.device_id)}}
    async def async_added_to_hass(self): self.async_on_remove(async_dispatcher_connect(self.hass, f"{SIGNAL_DEVICE_STATE}_{self._conn.device_id}", self._handle))
    @callback
    def _handle(self): self.async_write_ha_state()
class VoiceEnabledSwitch(_Base):
    _attr_name = "Enable Voice Assistant"; _attr_icon = "mdi:assistant"
    def __init__(self, c): super().__init__(c); self._attr_unique_id = f"{c.device_id}_voice_enabled"
    @property
    def is_on(self): return self._conn.voice_enabled
    async def async_turn_on(self, **kwargs): self._conn.voice_enabled = True; self._conn.set_phase(PHASE_IDLE); await self._conn.cmd_set_config({"voice_enabled": True})
    async def async_turn_off(self, **kwargs): self._conn.voice_enabled = False; self._conn.set_phase(PHASE_MUTED); await self._conn.cmd_set_config({"voice_enabled": False})
class ButtonClickSoundsSwitch(_Base):
    _attr_name = "Button click sounds"; _attr_icon = "mdi:bullhorn"; _attr_entity_category = "config"
    def __init__(self, c): super().__init__(c); self._attr_unique_id = f"{c.device_id}_button_sounds"
    @property
    def is_on(self): return self._conn.button_sounds
    async def async_turn_on(self, **kwargs): self._conn.button_sounds = True; await self._conn.cmd_set_config({"button_sounds": True})
    async def async_turn_off(self, **kwargs): self._conn.button_sounds = False; await self._conn.cmd_set_config({"button_sounds": False})
class WakeSoundSwitch(_Base):
    _attr_name = "Wake sound"; _attr_icon = "mdi:bullhorn"; _attr_entity_category = "config"
    def __init__(self, c): super().__init__(c); self._attr_unique_id = f"{c.device_id}_wake_sound"
    @property
    def is_on(self): return self._conn.wake_sound
    async def async_turn_on(self, **kwargs): self._conn.wake_sound = True; await self._conn.cmd_set_config({"wake_sound": True})
    async def async_turn_off(self, **kwargs): self._conn.wake_sound = False; await self._conn.cmd_set_config({"wake_sound": False})
class TimerRingingSwitch(_Base):
    _attr_name = "Time Ringing"; _attr_icon = "mdi:timer-alert"
    def __init__(self, c): super().__init__(c); self._attr_unique_id = f"{c.device_id}_timer_ringing"
    @property
    def is_on(self): return self._conn.timer_ringing
    async def async_turn_on(self, **kwargs): self._conn.timer_ringing = True; await self._conn.send_json({"type": "timer_ringing", "state": True})
    async def async_turn_off(self, **kwargs): self._conn.timer_ringing = False; await self._conn.send_json({"type": "timer_ringing", "state": False})
