"""DataUpdateCoordinator for Energi Fyn."""

import logging
import time
from datetime import datetime, timezone

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE_CONSUMPTION,
    API_BASE_PROFILE,
    API_BASE_SELF_SERVICE,
    CLIENT_ID,
    CLIENT_SECRET,
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRES,
    DOMAIN,
    TOKEN_URL,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class EnergiFynCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from Energi Fyn API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.entry = entry
        self.session = async_get_clientsession(hass)
        self._update_token_from_entry()

    def _update_token_from_entry(self):
        """Update local token variables from config entry."""
        self.access_token = self.entry.data[CONF_ACCESS_TOKEN]
        self.refresh_token = self.entry.data[CONF_REFRESH_TOKEN]
        self.expires_at = self.entry.data[CONF_TOKEN_EXPIRES]

    async def _refresh_access_token(self):
        """Refresh the access token using the refresh token."""
        _LOGGER.debug("Refreshing access token")

        try:
            with async_timeout.timeout(30):
                resp = await self.session.post(
                    TOKEN_URL,
                    data={
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                        "grant_type": "refresh_token",
                        "refresh_token": self.refresh_token,
                        "scope": "openid profile customer offline_access",
                    },
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Origin": "https://www.energifyn.dk",
                        "Referer": "https://www.energifyn.dk/",
                    },
                )

                if resp.status != 200:
                    raise UpdateFailed(f"Token refresh failed: {resp.status}")

                tokens = await resp.json()

                # Calculate new expiry (with 60s buffer)
                expires_at = time.time() + tokens["expires_in"] - 60

                # Update config entry to persist new tokens
                self.hass.config_entries.async_update_entry(
                    self.entry,
                    data={
                        **self.entry.data,
                        CONF_ACCESS_TOKEN: tokens["access_token"],
                        CONF_REFRESH_TOKEN: tokens.get(
                            "refresh_token", self.refresh_token
                        ),
                        CONF_TOKEN_EXPIRES: expires_at,
                    },
                )

                # Update local variables
                self._update_token_from_entry()
                _LOGGER.debug("Token refreshed successfully")

        except Exception as err:
            raise UpdateFailed(f"Failed to refresh token: {err}") from err

    async def _async_update_data(self) -> dict:
        """Fetch data from API."""
        # Check if token needs refresh
        if time.time() > self.expires_at:
            await self._refresh_access_token()

        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            with async_timeout.timeout(30):
                return await self._fetch_data(headers)

        except Exception as err:
            # If unauthorized, try refreshing once and retry
            if hasattr(err, "status") and err.status == 401:
                _LOGGER.debug("Got 401, attempting token refresh")
                await self._refresh_access_token()
                headers = {"Authorization": f"Bearer {self.access_token}"}
                return await self._fetch_data(headers)
            raise UpdateFailed(f"Error fetching data: {err}") from err

    async def _fetch_data(self, headers):
        """Fetch all consumption data."""
        # Step 1: Get customers
        resp = await self.session.get(
            f"{API_BASE_PROFILE}/customers/",
            headers=headers,
        )
        resp.raise_for_status()
        customers = await resp.json()

        if not customers:
            return {}

        all_consumption_data = {}

        for customer in customers:
            customer_number = customer["customerNumber"]

            # Step 2: Get estates
            resp = await self.session.get(
                f"{API_BASE_SELF_SERVICE}/customers/{customer_number}/estates",
                headers=headers,
            )
            resp.raise_for_status()
            estates = await resp.json()

            for estate in estates:
                if not estate.get("isActive"):
                    continue

                estate_id = estate["id"]

                # Step 3: Get products
                resp = await self.session.get(
                    f"{API_BASE_SELF_SERVICE}/customers/{customer_number}/estates/{estate_id}/products",
                    headers=headers,
                )
                resp.raise_for_status()
                products = await resp.json()

                for product in products:
                    installation_id = product.get("installationId")
                    meter_id = product.get("meterId")

                    if not installation_id or not meter_id:
                        continue

                    # Step 4: Get consumption
                    resp = await self.session.get(
                        f"{API_BASE_CONSUMPTION}/consumptions/{customer_number}/{estate_id}/{meter_id}/{installation_id}/null/total",
                        headers=headers,
                    )
                    resp.raise_for_status()
                    consumption = await resp.json()

                    unique_key = f"{customer_number}_{estate_id}_{meter_id}"
                    all_consumption_data[unique_key] = {
                        "customer": customer,
                        "estate": estate,
                        "product": product,
                        "consumption": consumption,
                        "ids": {
                            "customer_number": customer_number,
                            "estate_id": estate_id,
                            "meter_id": meter_id,
                            "installation_id": installation_id,
                        },
                    }

        return all_consumption_data
