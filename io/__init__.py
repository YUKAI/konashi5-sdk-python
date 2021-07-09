#!/usr/bin/env python3

import asyncio

from . import Gpio


class IO:
    def __init__(self, konashi):
        self._gpio = Gpio.Gpio(konashi)

    @property
    def gpio(self) -> Gpio.Gpio:
        return self._gpio

    async def _on_connect(self):
        await self._gpio._on_connect()
