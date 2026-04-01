"""Buttons for Energi Fyn."""

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    async_add_entities([EnergiFynRefreshButton(coordinator)])


class EnergiFynRefreshButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Energi Fyn Refresh"
        self._attr_unique_id = "energi_fyn_refresh"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
