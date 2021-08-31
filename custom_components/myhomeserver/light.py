from __future__ import annotations

from typing import Any, Mapping

import myhome.object
import voluptuous as vol
from myhome._gen.model.object_value_dimmer import ObjectValueDimmer
from myhome._gen.model.object_value_light import ObjectValueLight

import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (
    PLATFORM_SCHEMA,
    SUPPORT_BRIGHTNESS,
    LightEntity, ATTR_BRIGHTNESS,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

PARALLEL_UPDATES = 10

OPTIONAL_LIGHT_STATE_ATTRIBUTES = [
    "protocol_name",
    "protocol_config",
    "id_room",
    "id_zone",
]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_USERNAME, default="admin"): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
    }
)


async def async_setup_entry(
        hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """Set up MyHomeSERVER lights from a config entry."""
    hub = hass.data[DOMAIN][config_entry.entry_id]

    server_serial = await hub.get_server_serial()
    lights = [
        MyHomeServerLight(server_serial, light)
        for light in await hub.lights()
    ]

    if len(lights) > 0:
        async_add_entities(lights)

    return True


def myhomeserver_to_hass_brightness(value: int):
    """Convert MyHomeSERVER brightness (0..100) to hass format (0..255)"""
    return int((value / 100.0) * 255)


def hass_to_myhomeserver_brightness(value: int):
    """Convert hass brightness (0..100) to MyHomeSERVER format (0..255)"""
    return int((value / 255.0) * 100)


class MyHomeServerLight(LightEntity):
    def __init__(self, server_serial: str, light: myhome.object.Light | myhome.object.Dimmer):
        self._light = light
        self._server_serial = server_serial
        self._value: ObjectValueLight | ObjectValueDimmer | None = None

    @property
    def name(self) -> str | None:
        return self._light.name

    @property
    def supported_features(self) -> int:
        if isinstance(self._light, myhome.object.Dimmer):
            return SUPPORT_BRIGHTNESS
        return 0

    @property
    def unique_id(self) -> str | None:
        return "%s_%d" % (self._server_serial, self._light.id)

    @property
    def device_info(self) -> DeviceInfo | None:
        device_info = {
            "identifiers": {(DOMAIN, self._light.id)},
            "name": self.name,
        }

        if self._light.room and self._light.zone:
            device_info["suggested_area"] = self._light.zone.name + " / " + self._light.room.name.replace(
                self._light.zone.name, '').strip()

        return device_info

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        extra_state_attributes = {}

        for attribute_name in OPTIONAL_LIGHT_STATE_ATTRIBUTES:
            if attribute_name in self._light.object_info:
                extra_state_attributes[attribute_name] = self._light.object_info[attribute_name]
        return extra_state_attributes

    @property
    def is_on(self) -> bool:
        if isinstance(self._light, myhome.object.Dimmer):
            return self._value is not None and self._value.dimmer > 0
        return self._value is not None and self._value.power

    @property
    def brightness(self) -> int | None:
        if isinstance(self._light, myhome.object.Dimmer):
            return myhomeserver_to_hass_brightness(self._value.dimmer)
        return 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        if ATTR_BRIGHTNESS in kwargs and isinstance(self._light, myhome.object.Dimmer):
            brightness = hass_to_myhomeserver_brightness(kwargs[ATTR_BRIGHTNESS])
            await self._light.dim(brightness)
        await self._light.switch_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._light.switch_off()

    async def async_update(self):
        self._value = await self._light.get_value()
