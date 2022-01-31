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


KONASHI_UUID_BUILTIN_RGB_SET = "064d0403-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_BUILTIN_RGB_GET = "064d0404-8251-49d9-b6f3-f7ba35e5d0a1"


class _RGBLed(KonashiElementBase._KonashiElementBase):
    def __init__(self, konashi) -> None:
        super().__init__(konashi)
        self._cb = None

    def __str__(self):
        return f'KonashiRGBLed'

    def __repr__(self):
        return f'KonashiRGBLed()'


    async def _on_connect(self) -> None:
        await self._enable_notify(KONASHI_UUID_BUILTIN_RGB_GET, self._ntf_cb)


    def _ntf_cb(self, sender, data):
        d = struct.unpack("<ccccH", data)
        color = (d[0],d[1],d[2],d[3])
        if self._cb is not None:
            self._cb(color)
            self._cb = None


    async def set(self, r: int, g: int, b: int, a: int, duration: int, callback: Callable[[Tuple[int,int,int,int]], None] = None) -> None:
        """Set the color of the LED, transitioning during the specified duration.
        If a callback is provided, it will be called when the color transition has finished.

        Args:
            r (int): The Red color component (valid range is [0,255], the value is truncated if out of range).
            g (int): The Green color component (valid range is [0,255], the value is truncated if out of range).
            b (int): The Blue color component (valid range is [0,255], the value is truncated if out of range).
            a (int): The Alpha component (valid range is [0,255], the value is truncated if out of range).
            duration (int): The time to transition to the new color in milliseconds (valid range is [0,65535], the value is truncated if out of range).
            callback (Callable[[Tuple[int,int,int,int]], None], optional): The callback. Defaults to None.
                The function takes 1 parameter and returns nothing:
                    Tuple[int,int,int,int]: The current LED color in the form (red,green,blue,alpha).
        """
        b = bytearray([r&0xFF, g&0xFF, b&0xFF, a&0xFF, (duration&0x00FF), ((duration&0xFF00)>>8)])
        await self._write(KONASHI_UUID_BUILTIN_RGB_SET, b)
        if callback is not None:
            self._cb = callback
