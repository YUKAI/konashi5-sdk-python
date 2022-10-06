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


KONASHI_UUID_BUILTIN_PRESENCE = "00002ae2-0000-1000-8000-00805f9b34fb"


class _Presence(KonashiElementBase._KonashiElementBase):
    def __init__(self, konashi) -> None:
        super().__init__(konashi)
        self._cb = None

    def __str__(self):
        return f'KonashiPresence'

    def __repr__(self):
        return f'KonashiPresence()'


    async def _on_connect(self) -> None:
        pass


    def _ntf_cb(self, sender, data):
        d = struct.unpack("<?", data)
        pres = d[0]
        if self._cb is not None:
            self._cb(pres)


    async def set_callback(self, notify_callback: Callable[[bool], None]) -> None:
        """Set a callback for the presence sensor data.

        Args:
            notify_callback (Callable[[bool], None]): The callback.
                The function takes 1 parameter and returns nothing:
                    bool: True if presence is detected, False otherwise.
        """
        if notify_callback is not None:
            self._cb = notify_callback
            await self._enable_notify(KONASHI_UUID_BUILTIN_PRESENCE, self._ntf_cb)
        else:
            await self._disable_notify(KONASHI_UUID_BUILTIN_PRESENCE)
            self._cb = None
