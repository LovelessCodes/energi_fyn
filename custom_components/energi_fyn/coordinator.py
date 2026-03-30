"""DataUpdateCoordinator for Energi Fyn."""

import logging

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE_CONSUMPTION,
    API_BASE_PROFILE,
    API_BASE_SELF_SERVICE,
    CONF_TOKEN,
    DOMAIN,
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
        self.token = entry.data[CONF_TOKEN]

    async def _async_update_data(self) -> dict:
        """Fetch data from API."""
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            async with async_timeout.timeout(30):
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

                # Process each customer
                for customer in customers:
                    customer_number = customer["customerNumber"]

                    # Step 2: Get estates for customer
                    resp = await self.session.get(
                        f"{API_BASE_SELF_SERVICE}/customers/{customer_number}/estates",
                        headers=headers,
                    )
                    resp.raise_for_status()
                    estates = await resp.json()

                    for estate in estates:
                        estate_id = estate["id"]

                        # Step 3: Get products (contains meter info)
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

                            # Step 4: Get consumption data
                            resp = await self.session.get(
                                f"{API_BASE_CONSUMPTION}/consumptions/{customer_number}/{estate_id}/{meter_id}/{installation_id}/null/total",
                                headers=headers,
                            )
                            resp.raise_for_status()
                            consumption = await resp.json()

                            # Create unique key for this meter
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

        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
