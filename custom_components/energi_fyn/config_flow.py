"""Config flow for Energi Fyn."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_BASE_PROFILE, CONF_TOKEN, DOMAIN


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            token = user_input[CONF_TOKEN]
            session = async_get_clientsession(self.hass)

            # Validate token by fetching customers
            try:
                resp = await session.get(
                    f"{API_BASE_PROFILE}/customers/",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if resp.status == 200:
                    return self.async_create_entry(
                        title="Energi Fyn", data={CONF_TOKEN: token}
                    )
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            description_placeholders={"url": "https://www.energifyn.dk"},
            errors=errors,
        )
