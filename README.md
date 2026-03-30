# Energi Fyn for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![Home Assistant](https://img.shields.io/badge/home%20assistant-%3E%3D2026.3.4-blue.svg?style=for-the-badge)](https://www.home-assistant.io)

[![Open Home Assistant Community Store](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=LovelessCodes&repository=energi_fyn&category=integration)

Unofficial integration for **Energi Fyn** electricity consumption monitoring in Home Assistant. Track your household electricity usage directly from Energi Fyn's customer portal.

> **Note:** This integration is specifically for customers of [Energi Fyn](https://www.energifyn.dk/) (Denmark). If you're not a customer, this integration won't work for you.

## Features

- **Energy Dashboard integration** – Compatible with Home Assistant's native Energy Dashboard for complete home energy monitoring
- **Multi-estate support** – Automatically discovers all addresses and meters associated with your account
- **Real-time consumption** – Current total electricity consumption in kWh
- **Consumption statistics** – Min, max, and average values for your billing period
- **Product details** – Tariff information and subscription status for each installation
- **Automatic discovery** – Finds all active electricity contracts across your customer profile

## Installation

### Via HACS (Recommended)

1. Add this repository to HACS as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories):
  - Repository: `https://github.com/LovelessCodes/energi_fyn`
  - Category: Integration
2. Click **Download** in the HACS interface
3. Restart Home Assistant
4. Go to **Settings > Devices & Services > Add Integration** and search for "Energi Fyn"

### Manual Installation

1. Copy the `energi_fyn` folder from this repository into your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add the integration via the UI

## Configuration

### Getting Your API Token

Currently, this integration requires a manual API token extracted from your browser:

1. Log in to [Energi Fyn Min Side](https://www.energifyn.dk/min-side) portal
2. Open your browser's Developer Tools (F12)
3. Go to the **Network** tab
4. Refresh the page (F5)
5. Look for any API request (e.g., to `efselfserviceapi.azurewebsites.net` or `efprofileservice.azurewebsites.net`)
6. Copy the **Authorization** header value (the long string after `Bearer `)
7. Paste this token into the integration configuration

> **⚠️ Token Expiry:** The API token expires after 1 hour. A future update will add automatic refresh using your login credentials. For now, you'll need to re-configure the integration with a fresh token if it stops working.

## Available Sensors

For each electricity meter discovered, the following sensors are created:

| Sensor | Description | Unit | State Class |
|--------|-------------|------|-------------|
| **Consumption** | Total electricity consumption | kWh | `total_increasing` |

### Attributes

Each consumption sensor includes additional metadata:
- `product_name`: Your subscription type (e.g., "SpotEl")
- `tariff`: Tariff code (e.g., "EK-30")
- `subscription_state`: Active/Inactive status
- `unit`: Measurement unit (kWh)

## Energy Dashboard Setup

To track electricity consumption alongside your other energy sources:

1. Go to **Settings > Dashboards > Energy**
2. Under **Electricity Grid**, click **Add Consumption**
3. Select your Energi Fyn consumption sensor (e.g., `sensor.energi_fyn_address_electricity`)
4. The integration will automatically feed data into the Energy Dashboard

## Technical Details

This integration communicates with Energi Fyn's Azure-based API infrastructure:

- `GET /api/customers/` – Enumerate customer accounts
- `GET /api/customers/{id}/estates` – Discover properties/addresses
- `GET /api/customers/{id}/estates/{estate_id}/products` – Fetch meter and installation IDs
- `GET /api/consumptions/{...}/total` – Retrieve consumption statistics

**Data resolution:** The API provides total accumulated consumption values suitable for Energy Dashboard integration. Historical granular data (hourly/daily breakdowns) is not currently available through this API endpoint.

## Troubleshooting

### "Invalid authentication" error
- The token expires after 1 hour. Re-add the integration with a fresh token from your browser
- Ensure you copied the full token without the "Bearer " prefix

### Missing meters or estates
- Verify the address has an active electricity contract
- Check that the meter is registered in the Energi Fyn customer portal

### Sensors show "unavailable"
- Check Home Assistant logs for API connectivity issues
- Verify the estate is marked as `isActive: true` in your account

## Roadmap

- [ ] Automatic token refresh using email/password authentication
- [ ] Spot price integration for real-time electricity pricing

## Disclaimer

This is an unofficial integration and is not affiliated with or endorsed by Energi Fyn. Use at your own risk. Your API token is stored locally in your Home Assistant instance and is only used to communicate with Energi Fyn's official API endpoints.

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Monitor your electricity consumption with Home Assistant! ⚡**
