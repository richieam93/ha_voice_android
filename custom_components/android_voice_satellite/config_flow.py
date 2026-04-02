from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import CONF_API_KEY, CONF_CLIENT_ID, CONF_DEVICE_ID, CONF_DEVICE_NAME, DOMAIN


class AndroidVoiceSatelliteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        manager = self.hass.data[DOMAIN]["manager"]
        pending = manager.get_pending_devices()

        if user_input is not None:
            client_id = user_input["pending_device"]
            item = manager.pop_pending(client_id)
            if item is None:
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema({vol.Required("pending_device"): vol.In({})}),
                    errors={"base": "device_not_found"},
                )

            await self.async_set_unique_id(item.device_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=item.device_name,
                data={
                    CONF_DEVICE_NAME: item.device_name,
                    CONF_DEVICE_ID: item.device_id,
                    CONF_API_KEY: item.api_key,
                    CONF_CLIENT_ID: item.client_id,
                },
            )

        if not pending:
            return self.async_show_form(step_id="no_devices", data_schema=vol.Schema({}))

        options = {item.client_id: f"{item.device_name} ({item.device_model or 'Android'})" for item in pending}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("pending_device"): vol.In(options)}),
        )

    async def async_step_no_devices(self, user_input=None):
        return self.async_abort(reason="no_devices")

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
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
            description_placeholders={"api_key": self._entry.data.get(CONF_API_KEY, "")},
        )
