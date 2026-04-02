from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .connection import ensure_manager
from .const import CONF_API_KEY, CONF_CLIENT_ID, CONF_DEVICE_ID, CONF_DEVICE_NAME, DOMAIN


class AndroidVoiceSatelliteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        manager = await ensure_manager(self.hass)
        pair = manager.create_pairing_session()
        base = self.hass.config.external_url or self.hass.config.internal_url or "http://homeassistant.local:8123"
        self.context["pair_token"] = pair.pair_token
        return self.async_show_form(
            step_id="pair",
            data_schema=vol.Schema({}),
            description_placeholders={
                "pairing_page_url": manager.get_pairing_page_url(base, pair.pair_token),
                "pairing_payload": manager.get_pairing_payload(base, pair.pair_token),
            },
        )

    async def async_step_pair(self, user_input=None):
        manager = await ensure_manager(self.hass)
        pair_token = self.context.get("pair_token")
        pending = manager.get_pending_devices(pair_token=pair_token)
        if not pending:
            return self.async_show_form(
                step_id="pair",
                data_schema=vol.Schema({}),
                errors={"base": "no_devices"},
                description_placeholders={
                    "pairing_page_url": manager.get_pairing_page_url(self.hass.config.external_url or self.hass.config.internal_url or "http://homeassistant.local:8123", pair_token),
                    "pairing_payload": manager.get_pairing_payload(self.hass.config.external_url or self.hass.config.internal_url or "http://homeassistant.local:8123", pair_token),
                },
            )
        if len(pending) == 1:
            item = manager.pop_pending(pending[0].client_id)
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
        self.context["pair_token"] = pair_token
        options = {item.client_id: f"{item.device_name} ({item.device_model or 'Android'})" for item in pending}
        return self.async_show_form(
            step_id="select",
            data_schema=vol.Schema({vol.Required("pending_device"): vol.In(options)}),
        )

    async def async_step_select(self, user_input=None):
        manager = await ensure_manager(self.hass)
        item = manager.pop_pending(user_input["pending_device"])
        if item is None:
            return self.async_abort(reason="device_not_found")
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
