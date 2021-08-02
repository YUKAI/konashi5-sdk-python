#!/usr/bin/env python3

import asyncio

from . import Temperature
from . import Humidity
from . import Pressure


class Builtin:
    def __init__(self, konashi):
        self._temperature = Temperature.Temperature(konashi)
        self._humidity = Humidity.Humidity(konashi)
        self._pressure = Pressure.Pressure(konashi)
        self._presence = None
        self._accelgyro = None
        self._rgbled = None

    @property
    def temperature(self) -> Temperature.Temperature:
        return self._temperature

    @property
    def humidity(self) -> Humidity.Humidity:
        return self._humidity

    @property
    def pressure(self) -> Pressure.Pressure:
        return self._pressure

    async def _on_connect(self):
        await self._temperature._on_connect()
        await self._humidity._on_connect()
        await self._pressure._on_connect()
