"""Sensor platform for Energi Fyn."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = []

    for unique_key, data in coordinator.data.items():
        estate = data["estate"]
        product = data["product"]
        consumption = data["consumption"]

        # Create total consumption sensor
        entities.append(
            EnergiFynConsumptionSensor(
                coordinator, unique_key, estate, product, consumption
            )
        )

    async_add_entities(entities)


class EnergiFynConsumptionSensor(CoordinatorEntity, SensorEntity):
    """Sensor for electricity consumption."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, unique_key, estate, product, consumption):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.unique_key = unique_key

        estate_id = estate["id"]
        meter_id = product.get("meterId", "unknown")

        self._attr_unique_id = f"{DOMAIN}_{estate_id}_{meter_id}_consumption"
        self._attr_name = f"{estate['address']} Electricity"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{estate_id}_{meter_id}")},
            name=f"{estate['address']}",
            manufacturer="Energi Fyn",
            model=product.get("productName", "Electricity"),
            via_device=(DOMAIN, estate_id),
        )

    @property
    def native_value(self):
        """Return total consumption."""
        data = self.coordinator.data.get(self.unique_key, {})
        consumption = data.get("consumption", {})

        # Return the total from summary, or sum of items if no total
        summary = consumption.get("summary", {})
        total = summary.get("total")

        if total is not None:
            return float(total)

        # Fallback: sum of all items
        items = consumption.get("items", [])
        if items:
            return sum(float(item["value"]) for item in items if item.get("value"))

        return None

    @property
    def extra_state_attributes(self):
        """Return additional stats."""
        data = self.coordinator.data.get(self.unique_key, {})
        consumption = data.get("consumption", {})
        summary = consumption.get("summary", {})

        return {
            "average": summary.get("avg"),
            "minimum": summary.get("min"),
            "maximum": summary.get("max"),
            "unit": consumption.get("unit"),
            "product_name": data.get("product", {}).get("productName"),
            "tariff": data.get("product", {}).get("tarifArt"),
            "subscription_state": data.get("product", {}).get("subscriptionState"),
        }
