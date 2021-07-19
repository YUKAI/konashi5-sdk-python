#!/usr/bin/env python3

import asyncio

from . import System
from . import Bluetooth


class Settings:
    def __init__(self, konashi):
        self._system = System.System(konashi)
        self._bluetooth = Bluetooth.Bluetooth(konashi)

    @property
    def system(self) -> System.System:
        return self._system

    @property
    def bluetooth(self) -> Bluetooth.Bluetooth:
        return self._bluetooth

    async def _on_connect(self):
        await self._system._on_connect()
        await self._bluetooth._on_connect()
