#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import struct
from ctypes import *
from typing import *
from enum import *
import abc

from bleak import *

from .Errors import *


class _KonashiElementBase:
    def __init__(self, konashi):
        self._konashi = konashi

    async def _read(self, uuid: str) -> None:
        if self._konashi._ble_client is None:
            raise KonashiError(f'Connection is not established')
        try:
            await self._konashi._ble_client.read_gatt_char(uuid)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE read: "{str(e)}"')

    async def _write(self, uuid: str, data: bytes) -> None:
        if self._konashi._ble_client is None:
            raise KonashiError(f'Connection is not established')
        try:
            await self._konashi._ble_client.write_gatt_char(uuid, data)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE write: "{str(e)}"')

    async def _enable_notify(self, uuid: str, cb: Callable[[int, bytearray], None]) -> None:
        if self._konashi._ble_client is None:
            raise KonashiError(f'Connection is not established')
        try:
            await self._konashi._ble_client.start_notify(uuid, cb)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE notify start: "{str(e)}"')

    async def _disable_notify(self, uuid: str) -> None:
        if self._konashi._ble_client is None:
            raise KonashiError(f'Connection is not established')
        try:
            await self._konashi._ble_client.stop_notify(uuid)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE notify stop: "{str(e)}"')

    @abc.abstractmethod
    async def _on_connect(self) -> None:
        pass
