"""Config flow for Android Voice Assistant integration."""
from __future__ import annotations

from typing import Any
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlowWithConfigEntry
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from .const import CONF_DEVICE_NAME, DEFAULT_VOLUME, DEFAULT_WAKE_WORD_SENSITIVITY, DOMAIN, AlarmAction, STTEngine, TTSEngine, UITheme, WakeWordEngine, WakeWordModel

class AndroidVoiceAssistantConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input.get(CONF_DEVICE_NAME, "Android Voice Assistant"), data=user_input)
        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Optional(CONF_DEVICE_NAME, default="Android Voice Assistant"): cv.string}))
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithConfigEntry:
        return AndroidVoiceAssistantOptionsFlow(config_entry)

class AndroidVoiceAssistantOptionsFlow(OptionsFlowWithConfigEntry):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return self.async_show_menu(step_id="init", menu_options=["voice_settings", "audio_settings", "wake_word_settings", "tts_stt_settings", "timer_alarm_settings", "ui_theme_settings", "advanced_settings", "network_settings"])
    async def _simple_form(self, step_id: str, schema_dict: dict) -> FlowResult:
        return self.async_show_form(step_id=step_id, data_schema=vol.Schema(schema_dict))
    async def async_step_voice_settings(self, user_input=None):
        if user_input is not None: return self.async_create_entry(title="", data={**self.options, **user_input})
        o = self.options
        return await self._simple_form("voice_settings", {vol.Optional("voice_enabled", default=o.get("voice_enabled", True)): bool, vol.Optional("wake_sound_enabled", default=o.get("wake_sound_enabled", True)): bool, vol.Optional("button_sound_enabled", default=o.get("button_sound_enabled", True)): bool, vol.Optional("continuous_conversation", default=o.get("continuous_conversation", False)): bool, vol.Optional("vibrate_on_wake_word", default=o.get("vibrate_on_wake_word", True)): bool, vol.Optional("keep_screen_on_while_listening", default=o.get("keep_screen_on_while_listening", True)): bool, vol.Optional("show_transcript_notification", default=o.get("show_transcript_notification", True)): bool})
    async def async_step_audio_settings(self, user_input=None):
        if user_input is not None: return self.async_create_entry(title="", data={**self.options, **user_input})
        o = self.options
        return await self._simple_form("audio_settings", {vol.Optional("volume", default=o.get("volume", DEFAULT_VOLUME)): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)), vol.Optional("mic_gain", default=o.get("mic_gain", 1.0)): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=5.0))})
    async def async_step_wake_word_settings(self, user_input=None):
        if user_input is not None: return self.async_create_entry(title="", data={**self.options, **user_input})
        o = self.options
        return await self._simple_form("wake_word_settings", {vol.Optional("wake_word_engine", default=o.get("wake_word_engine", WakeWordEngine.PORCUPINE)): vol.In([e.value for e in WakeWordEngine]), vol.Optional("wake_word_model", default=o.get("wake_word_model", WakeWordModel.HEY_JARVIS)): vol.In([m.value for m in WakeWordModel]), vol.Optional("wake_word_sensitivity", default=o.get("wake_word_sensitivity", DEFAULT_WAKE_WORD_SENSITIVITY)): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)), vol.Optional("wake_word_custom_path", default=o.get("wake_word_custom_path", "")): cv.string})
    async def async_step_tts_stt_settings(self, user_input=None):
        if user_input is not None: return self.async_create_entry(title="", data={**self.options, **user_input})
        o = self.options
        return await self._simple_form("tts_stt_settings", {vol.Optional("stt_engine", default=o.get("stt_engine", STTEngine.HOME_ASSISTANT)): vol.In([e.value for e in STTEngine]), vol.Optional("tts_engine", default=o.get("tts_engine", TTSEngine.HOME_ASSISTANT)): vol.In([e.value for e in TTSEngine]), vol.Optional("stt_language", default=o.get("stt_language", "de")): cv.string, vol.Optional("tts_language", default=o.get("tts_language", "de")): cv.string})
    async def async_step_timer_alarm_settings(self, user_input=None):
        if user_input is not None: return self.async_create_entry(title="", data={**self.options, **user_input})
        return await self._simple_form("timer_alarm_settings", {vol.Optional("alarm_action", default=self.options.get("alarm_action", AlarmAction.SOUND_AND_EVENT)): vol.In([a.value for a in AlarmAction])})
    async def async_step_ui_theme_settings(self, user_input=None):
        if user_input is not None: return self.async_create_entry(title="", data={**self.options, **user_input})
        return await self._simple_form("ui_theme_settings", {vol.Optional("ui_theme", default=self.options.get("ui_theme", UITheme.DARK)): vol.In([t.value for t in UITheme])})
    async def async_step_advanced_settings(self, user_input=None):
        if user_input is not None: return self.async_create_entry(title="", data={**self.options, **user_input})
        return await self._simple_form("advanced_settings", {vol.Optional("auto_start_on_boot", default=self.options.get("auto_start_on_boot", True)): bool, vol.Optional("battery_saver_mode", default=self.options.get("battery_saver_mode", False)): bool})
    async def async_step_network_settings(self, user_input=None):
        if user_input is not None: return self.async_create_entry(title="", data={**self.options, **user_input})
        return await self._simple_form("network_settings", {vol.Optional("auto_reconnect", default=self.options.get("auto_reconnect", True)): bool})
