"""Config flow for MyHOMEServer integration."""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import ParseResult, urlparse

import myhome.client
from aiohttp import ClientError
from urllib3.exceptions import MaxRetryError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.ssdp import ATTR_SSDP_LOCATION
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.typing import DiscoveryInfoType

from .const import DOMAIN, LOGGER
from .exception import CannotConnect, InvalidAuth
from .hub import MyHomeServerHub

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    LOGGER.debug(f"Validating account {data[CONF_USERNAME]} at host {data[CONF_HOST]}")
    hub = MyHomeServerHub(data[CONF_HOST])

    if await hub.get_server_serial() is None:
        raise CannotConnect

    if not await hub.authenticate(data[CONF_USERNAME], data[CONF_PASSWORD]):
        raise InvalidAuth

    LOGGER.debug(
        "Account {} present at {} and authentication with provided password succeeded".format(
            data[CONF_USERNAME], data[CONF_HOST]
        )
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MyHOMEServer."""

    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._username: str | None = None
        self._password: str | None = None
        self._serial: str | None = None
        self._name: str | None = None

    async def _get_serial_for_host(self, host: str) -> str:
        client = myhome.client.Client(host)
        try:
            return await client.get_server_serial()
        except ClientError:
            raise CannotConnect

    async def async_step_ssdp(self, discovery_info: DiscoveryInfoType) -> FlowResult:
        """Handle a flow initialized by discovery."""
        ssdp_location: ParseResult = urlparse(discovery_info[ATTR_SSDP_LOCATION])
        self._host = ssdp_location.hostname
        self.context[CONF_HOST] = self._host
        self._serial = await self._get_serial_for_host(self._host)

        await self.async_set_unique_id(self._serial)
        self._abort_if_unique_id_configured({CONF_HOST: self._host})

        self._name = "MyHomeSERVER (" + self._serial + ")"

        return await self.async_step_confirm()

    async def async_step_confirm(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle user-confirmation of discovered node."""
        if user_input is None:
            return self._show_setup_form_confirm()

        user_input.update({CONF_HOST: self._host})
        await validate_input(self.hass, user_input)
        self._username = user_input[CONF_USERNAME]
        self._password = user_input[CONF_PASSWORD]

        return self._async_create_entry()

    def _async_create_entry(self):
        """Async create flow handler entry."""
        return self.async_create_entry(
            title=self._name,
            data={
                CONF_HOST: self._host,
                CONF_USERNAME: self._username,
                CONF_PASSWORD: self._password,
            },
        )

    def _show_setup_form_init(self, errors: dict[str, str] | None = None) -> FlowResult:
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors or {},
        )

    def _show_setup_form_confirm(
            self, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors or {},
        )

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self._show_setup_form_init()

        self._host = user_input[CONF_HOST]
        LOGGER.debug(f"user_input: {user_input!r}")
        LOGGER.debug(
            'User configuration: host="%s",username="%s",len(password)=%d'
            % (
                user_input[CONF_HOST],
                user_input[CONF_USERNAME],
                len(user_input[CONF_PASSWORD]),
            )
        )

        errors = {}

        try:
            LOGGER.debug(f"Attempting to retrieve serial from host {self._host}")
            self._serial = await self._get_serial_for_host(self._host)
            LOGGER.debug(f"Serial: {self._serial}")

            await self.async_set_unique_id(self._serial)
            self._abort_if_unique_id_configured({CONF_HOST: self._host})

            await validate_input(self.hass, user_input)
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self._async_create_entry()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
