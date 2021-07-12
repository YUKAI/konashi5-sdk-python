#!/usr/bin/env python3

import asyncio

from . import Gpio
from . import SoftPWM


class IO:
    def __init__(self, konashi):
        self._gpio = Gpio.Gpio(konashi)
        self._softpwm = SoftPWM.SoftPWM(konashi, self._gpio)

    @property
    def gpio(self) -> Gpio.Gpio:
        return self._gpio

    @property
    def softpwm(self) -> Gpio.Gpio:
        return self._softpwm

    async def _on_connect(self):
        await self._gpio._on_connect()
        await self._softpwm._on_connect()