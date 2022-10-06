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


KONASHI_UUID_BUILTIN_HUMIDITY = "00002a6f-0000-1000-8000-00805f9b34fb"


class _Humidity(KonashiElementBase._KonashiElementBase):
    def __init__(self, konashi) -> None:
        super().__init__(konashi)
        self._cb = None

    def __str__(self):
        return f'KonashiHumidity'

    def __repr__(self):
        return f'KonashiHumidity()'


    async def _on_connect(self) -> None:
        pass


    def _ntf_cb(self, sender, data):
        d = struct.unpack("<h", data)
        hum = d[0]
        hum /= 100
        if self._cb is not None:
            self._cb(hum)


    async def set_callback(self, notify_callback: Callable[[float], None]) -> None:
        """Set a callback for the humidity data.

        Args:
            notify_callback (Callable[[float], None]): The callback.
                The function takes 1 parameter and return nothing:
                    float: The humidity in %.
        """
        if notify_callback is not None:
            self._cb = notify_callback
            await self._enable_notify(KONASHI_UUID_BUILTIN_HUMIDITY, self._ntf_cb)
        else:
            await self._disable_notify(KONASHI_UUID_BUILTIN_HUMIDITY)
            self._cb = None
