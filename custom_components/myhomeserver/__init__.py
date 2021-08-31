"""The MyHOMEServer integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, LOGGER
from .hub import MyHomeServerHub

PLATFORMS = ["light"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up MyHomeServer component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MyHomeSERVER from a config entry."""
    hub = MyHomeServerHub(entry.data[CONF_HOST])

    if not await hub.authenticate(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]):
        return False

    hass.data[DOMAIN][entry.entry_id] = hub

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    hub: MyHomeServerHub = hass.data[DOMAIN][entry.entry_id]
    hub.client._client.rest_client._client_session.close()

    return unload_ok
