"""The Energi Fyn integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN
from .coordinator import EnergiFynCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    coordinator = EnergiFynCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    # Set up hourly refresh at minute 0
    _LOGGER.info("Setting up hourly refresh at minute=0, second=0")

    @callback
    def hourly_refresh_callback(now):
        """Wrapper to call the coordinator's refresh method."""
        _LOGGER.info("Time change callback triggered at %s", now)
        hass.async_create_task(coordinator.async_hourly_refresh(now))

    unsubscribe = async_track_time_change(
        hass,
        hourly_refresh_callback,
        minute=0,
        second=0,
    )
    _LOGGER.info("Hourly refresh setup complete")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "unsubscribe": unsubscribe,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        entry_data["unsubscribe"]()
    return unload_ok
