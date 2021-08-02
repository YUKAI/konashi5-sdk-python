#!/usr/bin/env python3

import asyncio

from . import Temperature


class Builtin:
    def __init__(self, konashi):
        self._temperature = Temperature.Temperature(konashi)
        self._humidity = None
        self._pressure = None
        self._presence = None
        self._accelgyro = None
        self._rgbled = None

    @property
    def temperature(self) -> Temperature.Temperature:
        return self._temperature

    async def _on_connect(self):
        await self._temperature._on_connect()
