"""Constants for Energi Fyn integration."""

from datetime import timedelta

DOMAIN = "energi_fyn"
CONF_TOKEN = "token"

# API Endpoints
API_BASE_PROFILE = "https://efprofileservice.azurewebsites.net/api"
API_BASE_SELF_SERVICE = "https://efselfserviceapi.azurewebsites.net/api"
API_BASE_CONSUMPTION = "https://efselfserviceapi.azurewebsites.net/api"

UPDATE_INTERVAL = timedelta(hours=6)
