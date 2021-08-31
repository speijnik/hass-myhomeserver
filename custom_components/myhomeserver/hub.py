"""Implementation of the MyHomeSERVER hub."""
from __future__ import annotations

import asyncio
import typing

import myhome.client
import myhome.object
from aiohttp import ClientError

from .const import LOGGER


class MyHomeServerHub:
    """MyHomeSERVER hub implementation."""

    def __init__(self, host: str) -> None:
        """Initialize."""
        self.host = host
        self.client = myhome.client.Client(host)
        self._object_list: myhome.object.ObjectList | None = None
        self._object_list_mutex = asyncio.Lock()

    async def get_object_list(self) -> myhome.object.ObjectList:
        async with self._object_list_mutex:
            if not self._object_list:
                self._object_list = await self.client.get_object_list()

        return self._object_list

    async def update_object_list(self) -> myhome.object.ObjectList:
        async with self._object_list_mutex:
            self._object_list = None
        return await self.get_object_list()

    async def authenticate(self, username: str, password: str) -> bool:
        """Test if we can authenticate with the host."""
        try:
            await self.client.login(username, password)
            return True
        except (myhome.client.LoginDenied, myhome.client.RemoteAccessDenied):
            return False

    async def get_server_serial(self) -> str | None:
        """Test if we have working HTTP connectivity."""
        try:
            return await self.client.get_server_serial()
        except ClientError as e:
            LOGGER.debug('Ignored client error %s while retrieving server serial' % (e,))
            return None

    async def lights(self) -> typing.Iterable[myhome.object.Light]:
        lights: list[myhome.object.Light] = []
        object_list = await self.get_object_list()

        for o in object_list.filter(type="light"):
            if isinstance(o, myhome.object.Light):
                lights.append(o)
        return lights
