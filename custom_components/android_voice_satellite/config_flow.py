from __future__ import annotations

import secrets
import uuid
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_DEVICE_NAME, CONF_DEVICE_ID, CONF_API_KEY

class AndroidVoiceSatelliteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self._device_name = user_input[CONF_DEVICE_NAME]
            self._device_id = uuid.uuid4().hex[:12]
            self._api_key = secrets.token_hex(32)
            await self.async_set_unique_id(self._device_id)
            self._abort_if_unique_id_configured()
            return await self.async_step_show_key()
        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Required(CONF_DEVICE_NAME, default="Android Satellite"): str}))

    async def async_step_show_key(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=self._device_name, data={CONF_DEVICE_NAME: self._device_name, CONF_DEVICE_ID: self._device_id, CONF_API_KEY: self._api_key})
        base = self.hass.config.external_url or self.hass.config.internal_url or "http://homeassistant.local:8123"
        return self.async_show_form(step_id="show_key", data_schema=vol.Schema({}), description_placeholders={"device_name": self._device_name, "api_key": self._api_key, "ws_url": f"{base}/api/android_voice_satellite/ws"})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return AndroidVoiceSatelliteOptionsFlow(config_entry)

class AndroidVoiceSatelliteOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init", data_schema=vol.Schema({}), description_placeholders={"api_key": self._entry.data.get(CONF_API_KEY, "")})
