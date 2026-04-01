"""Android Voice Assistant integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .const import (
    ATTR_ACTIVE_TIMERS,
    ATTR_APP_VERSION,
    ATTR_BATTERY_CHARGING,
    ATTR_BATTERY_LEVEL,
    ATTR_DEVICE_MODEL,
    ATTR_IS_MUTED,
    ATTR_LAST_ERROR,
    ATTR_LAST_STT_TEXT,
    ATTR_LAST_TTS_TEXT,
    ATTR_LAST_WAKE_WORD,
    ATTR_MIC_GAIN,
    ATTR_PHASE,
    ATTR_PHASE_NAME,
    ATTR_PIPELINE_ID,
    ATTR_UPTIME,
    ATTR_VOLUME,
    ATTR_WAKE_WORD_ENGINE,
    ATTR_WAKE_WORD_MODEL,
    ATTR_WIFI_SIGNAL,
    DEFAULT_AUTO_GAIN,
    DEFAULT_MAX_LISTEN_TIME,
    DEFAULT_MIC_GAIN,
    DEFAULT_NOISE_SUPPRESSION,
    DEFAULT_RECONNECT_INTERVAL,
    DEFAULT_SILENCE_TIMEOUT,
    DEFAULT_TIMER_RING_DURATION,
    DEFAULT_TIMER_SOUND,
    DEFAULT_VAD_SENSITIVITY,
    DEFAULT_VOLUME,
    DEFAULT_VOLUME_MAX,
    DEFAULT_VOLUME_MIN,
    DEFAULT_VOLUME_STEP,
    DEFAULT_WAKE_WORD_SENSITIVITY,
    DOMAIN,
    EVENT_DEVICE_CONNECTED,
    EVENT_DEVICE_DISCONNECTED,
    EVENT_PHASE_CHANGED,
    PHASE_NAMES,
    PLATFORMS,
    SIGNAL_CONFIG_CHANGED,
    SIGNAL_DEVICE_UPDATE,
    STORAGE_KEY,
    STORAGE_VERSION,
    AlarmAction,
    STTEngine,
    TTSEngine,
    UITheme,
    VoicePhase,
    WakeWordEngine,
    WakeWordModel,
)
from .websocket_api import async_register_websocket_api

_LOGGER = logging.getLogger(__name__)

class AndroidVoiceDevice:
    def __init__(self, hass: HomeAssistant, device_id: str, name: str, config: dict[str, Any] | None = None) -> None:
        self.hass = hass
        self.device_id = device_id
        self.name = name
        self._connected = False
        self.state: dict[str, Any] = {
            ATTR_PHASE: VoicePhase.NOT_READY,
            ATTR_PHASE_NAME: PHASE_NAMES[VoicePhase.NOT_READY],
            ATTR_LAST_WAKE_WORD: "",
            ATTR_LAST_STT_TEXT: "",
            ATTR_LAST_TTS_TEXT: "",
            ATTR_LAST_ERROR: "",
            ATTR_VOLUME: DEFAULT_VOLUME,
            ATTR_IS_MUTED: False,
            ATTR_BATTERY_LEVEL: -1,
            ATTR_BATTERY_CHARGING: False,
            ATTR_WIFI_SIGNAL: -1,
            ATTR_ACTIVE_TIMERS: [],
            ATTR_UPTIME: 0,
            ATTR_APP_VERSION: "unknown",
            ATTR_DEVICE_MODEL: "unknown",
            ATTR_WAKE_WORD_ENGINE: WakeWordEngine.PORCUPINE,
            ATTR_WAKE_WORD_MODEL: WakeWordModel.HEY_JARVIS,
            ATTR_PIPELINE_ID: None,
            ATTR_MIC_GAIN: DEFAULT_MIC_GAIN,
        }
        self.config: dict[str, Any] = config or self._default_config()

    @staticmethod
    def _default_config() -> dict[str, Any]:
        return {
            "voice_enabled": True,
            "wake_word_engine": WakeWordEngine.PORCUPINE,
            "wake_word_model": WakeWordModel.HEY_JARVIS,
            "wake_word_sensitivity": DEFAULT_WAKE_WORD_SENSITIVITY,
            "wake_word_custom_path": "",
            "wake_sound_enabled": True,
            "button_sound_enabled": True,
            "volume": DEFAULT_VOLUME,
            "volume_min": DEFAULT_VOLUME_MIN,
            "volume_max": DEFAULT_VOLUME_MAX,
            "volume_step": DEFAULT_VOLUME_STEP,
            "mic_gain": DEFAULT_MIC_GAIN,
            "noise_suppression_level": DEFAULT_NOISE_SUPPRESSION,
            "auto_gain_dbfs": DEFAULT_AUTO_GAIN,
            "vad_sensitivity": DEFAULT_VAD_SENSITIVITY,
            "silence_timeout_seconds": DEFAULT_SILENCE_TIMEOUT,
            "max_listen_time_seconds": DEFAULT_MAX_LISTEN_TIME,
            "stt_engine": STTEngine.HOME_ASSISTANT,
            "stt_language": "de",
            "tts_engine": TTSEngine.HOME_ASSISTANT,
            "tts_language": "de",
            "tts_voice": "",
            "pipeline_id": "",
            "conversation_agent": "",
            "alarm_action": AlarmAction.SOUND_AND_EVENT,
            "timer_ring_duration_seconds": DEFAULT_TIMER_RING_DURATION,
            "timer_sound": DEFAULT_TIMER_SOUND,
            "alarm_sound": DEFAULT_TIMER_SOUND,
            "reconnect_interval_seconds": DEFAULT_RECONNECT_INTERVAL,
            "auto_reconnect": True,
            "ui_theme": UITheme.DARK,
            "led_idle_color": "#00C853",
            "led_listening_color": "#FF33FF",
            "led_thinking_color": "#FF33FF",
            "led_replying_color": "#33FFFF",
            "led_error_color": "#FF0000",
            "led_not_ready_color": "#FF0000",
            "led_muted_color": "#E6E633",
            "led_timer_color": "#00FF00",
            "led_brightness": 0.8,
            "show_transcript_notification": True,
            "vibrate_on_wake_word": True,
            "keep_screen_on_while_listening": True,
            "continuous_conversation": False,
            "auto_start_on_boot": True,
            "battery_saver_mode": False,
            "battery_saver_threshold": 20,
            "do_not_disturb_start": "",
            "do_not_disturb_end": "",
            "allowed_areas": [],
            "media_player_entity": "",
        }

    @property
    def is_connected(self) -> bool:
        return self._connected

    @callback
    def set_connected(self, connected: bool) -> None:
        old = self._connected
        self._connected = connected
        if old != connected:
            self.hass.bus.async_fire(EVENT_DEVICE_CONNECTED if connected else EVENT_DEVICE_DISCONNECTED, {"device_id": self.device_id})
            self._notify_update()

    @callback
    def update_state(self, new_state: dict[str, Any]) -> None:
        old_phase = self.state.get(ATTR_PHASE)
        self.state.update(new_state)
        phase = self.state.get(ATTR_PHASE)
        if isinstance(phase, int):
            try:
                phase_enum = VoicePhase(phase)
                self.state[ATTR_PHASE_NAME] = PHASE_NAMES.get(phase_enum, f"Unbekannt ({phase})")
            except ValueError:
                self.state[ATTR_PHASE_NAME] = f"Unbekannt ({phase})"
        if old_phase != phase:
            self.hass.bus.async_fire(EVENT_PHASE_CHANGED, {"device_id": self.device_id, "old_phase": old_phase, "new_phase": phase, "phase_name": self.state.get(ATTR_PHASE_NAME, "")})
        self._notify_update()

    @callback
    def update_config(self, new_config: dict[str, Any]) -> None:
        self.config.update(new_config)
        async_dispatcher_send(self.hass, SIGNAL_CONFIG_CHANGED.format(device_id=self.device_id), self.config)
        self._notify_update()

    @callback
    def _notify_update(self) -> None:
        async_dispatcher_send(self.hass, SIGNAL_DEVICE_UPDATE.format(device_id=self.device_id))

class AndroidVoiceCoordinator:
    _config_entry_id: str = ""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.devices: dict[str, AndroidVoiceDevice] = {}
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)

    async def async_load(self) -> None:
        data = await self._store.async_load()
        if data and "devices" in data:
            for dev_data in data["devices"]:
                device_id = dev_data["device_id"]
                name = dev_data.get("name", device_id)
                config = dev_data.get("config", {})
                merged = AndroidVoiceDevice._default_config()
                merged.update(config)
                self.devices[device_id] = AndroidVoiceDevice(self.hass, device_id, name, merged)

    async def async_save(self) -> None:
        await self._store.async_save({"devices": [{"device_id": dev.device_id, "name": dev.name, "config": dev.config} for dev in self.devices.values()]})

    @callback
    def register_device(self, device_id: str, name: str, device_info: dict[str, Any] | None = None) -> AndroidVoiceDevice:
        if device_id in self.devices:
            device = self.devices[device_id]
            device.name = name
            if device_info:
                device.update_state(device_info)
            device.set_connected(True)
            return device
        device = AndroidVoiceDevice(self.hass, device_id, name)
        if device_info:
            device.update_state(device_info)
        device.set_connected(True)
        self.devices[device_id] = device
        dev_reg = dr.async_get(self.hass)
        dev_reg.async_get_or_create(config_entry_id=self._config_entry_id, identifiers={(DOMAIN, device_id)}, name=name, manufacturer="Android Voice Assistant", model=(device_info or {}).get(ATTR_DEVICE_MODEL, "Android"), sw_version=(device_info or {}).get(ATTR_APP_VERSION, "unknown"))
        self.hass.async_create_task(self.async_save())
        return device

    def get_device(self, device_id: str) -> AndroidVoiceDevice | None:
        return self.devices.get(device_id)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = AndroidVoiceCoordinator(hass)
    coordinator._config_entry_id = entry.entry_id
    await coordinator.async_load()
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    async_register_websocket_api(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
