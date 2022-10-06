#!/usr/bin/env python3

import asyncio

from . import GPIO
from . import SoftPWM
from . import HardPWM
from . import AIO
from . import I2C
from . import UART
from . import SPI


class _Io:
    def __init__(self, konashi):
        self._gpio = GPIO._GPIO(konashi)
        self._softpwm = SoftPWM._SoftPWM(konashi, self._gpio)
        self._hardpwm = HardPWM._HardPWM(konashi, self._gpio)
        self._analog = AIO._AIO(konashi)
        self._i2c = I2C._I2C(konashi, self._gpio)
        self._uart = UART._UART(konashi)
        self._spi = SPI._SPI(konashi, self._gpio)

    @property
    def gpio(self) -> GPIO._GPIO:
        """This Konashi devices GPIO interface.
        """
        return self._gpio

    @property
    def softpwm(self) -> SoftPWM._SoftPWM:
        """This Konashi devices Software PWM interface.
        """
        return self._softpwm

    @property
    def hardpwm(self) -> HardPWM._HardPWM:
        """This Konashi devices Hardware PWM interface.
        """
        return self._hardpwm

    @property
    def analog(self) -> AIO._AIO:
        """This Konashi devices AIO interface.
        """
        return self._analog

    @property
    def i2c(self) -> I2C._I2C:
        """This Konashi devices I2C interface.
        """
        return self._i2c

    @property
    def uart(self) -> UART._UART:
        """This Konashi devices UART interface.
        """
        return self._uart

    @property
    def spi(self) -> SPI._SPI:
        """This Konashi devices SPI interface.
        """
        return self._spi

    async def _on_connect(self):
        await self._gpio._on_connect()
        await self._softpwm._on_connect()
        await self._hardpwm._on_connect()
        await self._analog._on_connect()
        await self._i2c._on_connect()
        await self._uart._on_connect()
        await self._spi._on_connect()
