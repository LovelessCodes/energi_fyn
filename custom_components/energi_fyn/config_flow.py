"""Config flow for Energi Fyn."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_BASE_PROFILE,
    CLIENT_ID,
    CLIENT_SECRET,
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRES,
    DOMAIN,
    TOKEN_URL,
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            refresh_token = user_input[CONF_REFRESH_TOKEN]
            session = async_get_clientsession(self.hass)

            try:
                # Exchange refresh token for access token to validate
                resp = await session.post(
                    TOKEN_URL,
                    data={
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "scope": "openid profile customer offline_access",
                    },
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Origin": "https://www.energifyn.dk",
                        "Referer": "https://www.energifyn.dk/",
                    },
                )

                if resp.status != 200:
                    errors["base"] = "invalid_auth"
                else:
                    tokens = await resp.json()

                    # Calculate expiry timestamp with buffer
                    import time

                    expires_at = time.time() + tokens["expires_in"] - 60

                    # Test the token works
                    access_token = tokens["access_token"]
                    test_resp = await session.get(
                        f"{API_BASE_PROFILE}/customers/",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )

                    if test_resp.status != 200:
                        errors["base"] = "cannot_connect"
                    else:
                        return self.async_create_entry(
                            title="Energi Fyn",
                            data={
                                CONF_REFRESH_TOKEN: tokens.get(
                                    "refresh_token", refresh_token
                                ),
                                CONF_ACCESS_TOKEN: access_token,
                                CONF_TOKEN_EXPIRES: expires_at,
                            },
                        )

            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_REFRESH_TOKEN): str,
                }
            ),
            description_placeholders={
                "storage_key": "oidc.user:https://accounts.forsyningslogin.dk:ef-spa",
                "url": "https://www.energifyn.dk",
            },
            errors=errors,
        )
