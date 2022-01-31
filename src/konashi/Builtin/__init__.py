#!/usr/bin/env python3

import asyncio
import logging
from ctypes import *

from .. import KonashiElementBase
from . import Temperature
from . import Humidity
from . import Pressure
from . import Presence
from . import AccelGyro
from . import RGBLed


logger = logging.getLogger(__name__)


KONASHI_UUID_BUILTIN_VERSION = "064d0401-8251-49d9-b6f3-f7ba35e5d0a1"


class _Builtin(KonashiElementBase._KonashiElementBase):
    def __init__(self, konashi):
        super().__init__(konashi)
        self._temperature = Temperature._Temperature(konashi)
        self._humidity = Humidity._Humidity(konashi)
        self._pressure = Pressure._Pressure(konashi)
        self._presence = Presence._Presence(konashi)
        self._accelgyro = AccelGyro._AccelGyro(konashi)
        self._rgbled = RGBLed._RGBLed(konashi)
        self._version = -1

    @property
    def temperature(self) -> Temperature._Temperature:
        """This Konashi devices temperature sensor interface.
        """
        return self._temperature

    @property
    def humidity(self) -> Humidity._Humidity:
        """This Konashi devices humidity sendor interface.
        """
        return self._humidity

    @property
    def pressure(self) -> Pressure._Pressure:
        """This Konashi devices pressure sensor interface.
        """
        return self._pressure

    @property
    def presence(self) -> Presence._Presence:
        """This Konashi devices presence sensor interface.
        """
        return self._presence

    @property
    def accelgyro(self) -> AccelGyro._AccelGyro:
        """This Konashi devices Accel and Gyro sensor interface.
        """
        return self._accelgyro

    @property
    def rgbled(self) -> RGBLed._RGBLed:
        """This Konashi devices RGB LED interface.
        """
        return self._rgbled

    async def _on_connect(self):
        await self._enable_notify(KONASHI_UUID_BUILTIN_VERSION, self._ntf_cb_version)
        await self._read(KONASHI_UUID_BUILTIN_VERSION)
        await self._temperature._on_connect()
        await self._humidity._on_connect()
        await self._pressure._on_connect()
        await self._presence._on_connect()
        await self._accelgyro._on_connect()
        await self._rgbled._on_connect()

    def _ntf_cb_version(self, sender, data):
        logger.debug("Received konashi built-in version: {}".format("".join("{:02x}".format(x) for x in data)))
        new_version = int.from_bytes(data, byteorder='little', signed=True)
        if new_version != self._version:
            logger.debug("Konashi Built-in version change: {} -> {}".format(self._version, new_version))
            self._version = new_version
            if self._version == 0:
                logger.warn("Konashi base board unknown version")
            elif self._version == 1:
                logger.info("Konashi base board connected")
            else:
                logger.info("No base board connected")
