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


KONASHI_UUID_BUILTIN_ACCELGYRO = "064d0402-8251-49d9-b6f3-f7ba35e5d0a1"


class _AccelGyro(KonashiElementBase._KonashiElementBase):
    def __init__(self, konashi) -> None:
        super().__init__(konashi)
        self._cb = None

    def __str__(self):
        return f'KonashiAccelGyro'

    def __repr__(self):
        return f'KonashiAccelGyro()'


    async def _on_connect(self) -> None:
        pass


    def _ntf_cb(self, sender, data):
        d = struct.unpack("<hhhhhh", data)
        accel_x = d[0] / 32768 * 8
        accel_y = d[1] / 32768 * 8
        accel_z = d[2] / 32768 * 8
        gyro_x = d[3] / 32768 * 1000
        gyro_y = d[4] / 32768 * 1000
        gyro_z = d[5] / 32768 * 1000
        if self._cb is not None:
            self._cb((accel_x,accel_y,accel_z),(gyro_x,gyro_y,gyro_z))


    async def set_callback(self, notify_callback: Callable[[Tuple[float,float,float],Tuple[float,float,float]], None]) -> None:
        """Set the callback for the accelerometer and gyroscope data.

        Args:
            notify_callback (Callable[[Tuple[float,float,float],Tuple[float,float,float]], None]): The callback.
                The function take 2 parameters and returns nothing:
                    Tuple[float,float,float]: The acceleration in g (9.8 m/s^2).
                    Tuple[float,float,float]: The angular speed in degree/s.
        """
        if notify_callback is not None:
            self._cb = notify_callback
            await self._enable_notify(KONASHI_UUID_BUILTIN_ACCELGYRO, self._ntf_cb)
        else:
            await self._disable_notify(KONASHI_UUID_BUILTIN_ACCELGYRO)
            self._cb = None
