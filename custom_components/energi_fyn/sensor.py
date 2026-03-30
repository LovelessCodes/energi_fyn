"""Sensor platform for Energi Fyn."""

from datetime import datetime

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

        entities.append(EnergiFynPriceSensor(coordinator, unique_key, estate, product))

    async_add_entities(entities)


class EnergiFynPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor for current electricity price."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "DKK/kWh"  # Danish Krone per kWh

    def __init__(self, coordinator, unique_key, estate, product):
        super().__init__(coordinator)
        self.unique_key = unique_key

        estate_id = estate["id"]
        meter_id = product.get("meterId", "unknown")

        self._attr_unique_id = f"{DOMAIN}_{estate_id}_{meter_id}_current_price"
        self._attr_name = f"{estate['address']} Current Price"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{estate_id}_{meter_id}")},
            name=f"{estate['address']}",
            manufacturer="Energi Fyn",
            model=product.get("productName", "Electricity"),
        )

    @property
    def native_value(self):
        """Return current hour's price."""
        data = self.coordinator.data.get(self.unique_key, {})
        price_data = data.get("price_data", {})

        # Use the pre-calculated current price
        current_price = price_data.get("currentCustomerPowerPrice")
        if current_price is not None:
            return round(float(current_price), 4)

        # Fallback: calculate from hourly list if current is missing
        customer_prices = price_data.get("customerPrices", {})
        if not customer_prices:
            return None

        # Get today's date key (YYYY-MM-DD)
        today = datetime.now().strftime("%Y-%m-%d")
        today_data = customer_prices.get(f"{today}T00:00:00") or customer_prices.get(
            today
        )

        if not today_data:
            return None

        # Find current hour
        current_hour = datetime.now().hour
        prices = today_data.get("prices", [])

        for hour_data in prices:
            hour_str = hour_data.get("hour", "")
            if hour_str.startswith(f"{today}T{current_hour:02d}"):
                return round(
                    float(hour_data.get("price", 0) + hour_data.get("tarifPrice", 0)), 4
                )

        return None

    @property
    def extra_state_attributes(self):
        """Return price statistics and forecast."""
        data = self.coordinator.data.get(self.unique_key, {})
        price_data = data.get("price_data", {})
        customer_prices = price_data.get("customerPrices", {})

        if not customer_prices:
            return {}

        today = datetime.now().strftime("%Y-%m-%d")
        today_key = next(
            (k for k in customer_prices.keys() if k.startswith(today)), None
        )

        if not today_key:
            return {}

        today_data = customer_prices[today_key]
        summary = today_data.get("summary", {})
        prices = today_data.get("prices", [])

        # Build hourly forecast list
        price_forecast = [
            {
                "hour": p["hour"],
                "price": p["price"],
                "tarifPrice": p["tarifPrice"],
                "total": round(p["price"] + p.get("tarifPrice", 0), 4),
            }
            for p in prices
        ]

        return {
            "min_price": summary.get("min"),
            "max_price": summary.get("max"),
            "avg_price": summary.get("avg"),
            "price_forecast": price_forecast,
            "currency": "DKK",
            "includes_tariff": False,  # Raw spot price
        }


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
