#!/usr/bin/env python3

import asyncio

from . import System
from . import Bluetooth


class _Settings:
    def __init__(self, konashi):
        self._system = System._System(konashi)
        self._bluetooth = Bluetooth._Bluetooth(konashi)

    @property
    def system(self) -> System._System:
        """This Konashi devices System Settings interface.
        """
        return self._system

    @property
    def bluetooth(self) -> Bluetooth._Bluetooth:
        """This Konashi devices Bluetooth Settings interface.
        """
        return self._bluetooth

    async def _on_connect(self):
        await self._system._on_connect()
        await self._bluetooth._on_connect()
