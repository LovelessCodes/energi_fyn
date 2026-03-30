"""Constants for Energi Fyn integration."""

from datetime import timedelta

DOMAIN = "energi_fyn"

# Config keys
CONF_REFRESH_TOKEN = "refresh_token"
CONF_ACCESS_TOKEN = "access_token"
CONF_TOKEN_EXPIRES = "token_expires"  # Unix timestamp

# API Endpoints
API_BASE_PROFILE = "https://efprofileservice.azurewebsites.net/api"
API_BASE_SELF_SERVICE = "https://efselfserviceapi.azurewebsites.net/api"
API_BASE_CONSUMPTION = "https://efselfserviceapi.azurewebsites.net/api"
TOKEN_URL = "https://accounts.forsyningslogin.dk/connect/token"

# OAuth2 client credentials (public SPA client)
CLIENT_ID = "ef-spa"
CLIENT_SECRET = "ba312321-6a7c-470e-a5c9-def33ce42797"

UPDATE_INTERVAL = timedelta(hours=6)
TOKEN_REFRESH_BUFFER = 60  # Refresh 60 seconds before expiry
