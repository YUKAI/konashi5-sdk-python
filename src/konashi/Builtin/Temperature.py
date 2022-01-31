#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import struct
from ctypes import *
from typing import *
from enum import *

from bleak import *

from .. import KonashiElementBase
from ..Errors import *


KONASHI_UUID_BUILTIN_TEMPERATURE = "00002a6e-0000-1000-8000-00805f9b34fb"


class _Temperature(KonashiElementBase._KonashiElementBase):
    def __init__(self, konashi) -> None:
        super().__init__(konashi)
        self._cb = None

    def __str__(self):
        return f'KonashiTemperature'

    def __repr__(self):
        return f'KonashiTemperature()'


    async def _on_connect(self) -> None:
        pass


    def _ntf_cb(self, sender, data):
        d = struct.unpack("<h", data)
        temp = d[0]
        temp /= 100
        if self._cb is not None:
            self._cb(temp)


    async def set_callback(self, notify_callback: Callable[[float], None]) -> None:
        """Set a callback for the temperature sensor data.

        Args:
            notify_callback (Callable[[float], None]): The callback.
                The function takes 1 parameter and returns nothing:
                    float: The temperature in degrees Celsius.
        """
        if notify_callback is not None:
            self._cb = notify_callback
            await self._enable_notify(KONASHI_UUID_BUILTIN_TEMPERATURE, self._ntf_cb)
        else:
            await self._disable_notify(KONASHI_UUID_BUILTIN_TEMPERATURE)
            self._cb = None
