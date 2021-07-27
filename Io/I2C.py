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
from . import Gpio


KONASHI_UUID_CONFIG_CMD = "064d0201-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_CFG_CMD_I2C = 0x05
KONASHI_UUID_I2C_CONFIG_GET = "064d0206-8251-49d9-b6f3-f7ba35e5d0a1"

KONASHI_UUID_CONTROL_CMD = "064d0301-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_CTL_CMD_I2C_DATA = 0x05
KONASHI_UUID_I2C_DATA_IN = "064d0308-8251-49d9-b6f3-f7ba35e5d0a1"


class Mode(IntEnum):
    STANDARD = 0
    FAST = 1
class Config(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('mode', c_uint8, 1),
        ('enabled', c_uint8, 1),
        ('', c_uint8, 6)
    ]
    def __init__(self, enable: bool, mode: Mode) -> None:
        self.enabled = enable
        self.mode = mode
    def __str__(self):
        s = "KonashiI2CConfig("
        if self.enabled:
            s += "enabled"
        else:
            s += "disabled"
        s += ", mode:"
        if self.mode == Mode.STANDARD:
            s += "standard"
        elif self.mode == Mode.FAST:
            s += "fast"
        else:
            s += "unknown"
        s += ")"
        return s

class Operation(IntEnum):
    WRITE = 0
    READ = 1
    WRITE_READ = 2


class I2C(KonashiElementBase._KonashiElementBase):
    def __init__(self, konashi, gpio) -> None:
        super().__init__(konashi)
        self._gpio = gpio
        self._config = Config(False, Mode.STANDARD)
        self._trans_end_cb = None
        self._ongoing_control = []

    def __str__(self):
        return f'KonashiHardPWM'

    def __repr__(self):
        return f'KonashiHardPWM()'


    async def _on_connect(self) -> None:
        await self._enable_notify(KONASHI_UUID_I2C_CONFIG_GET, self._ntf_cb_config)
        await self._read(KONASHI_UUID_I2C_CONFIG_GET)
        await self._enable_notify(KONASHI_UUID_I2C_DATA_IN, self._ntf_cb_data_in)


    def _ntf_cb_config(self, sender, data):
        self._config = Config.from_buffer_copy(data)

    def _ntf_cb_data_in(self, sender, data):
        pass


    async def config(self, config: Config) -> None:
        """
        Configure the I2C peripheral.
          config: the I2C configuration
        """
        b = bytearray([KONASHI_CFG_CMD_I2C]) + bytearray(config)
        await self._write(KONASHI_UUID_CONFIG_CMD, b)

    async def get_config(self) -> Config:
        await self._read(KONASHI_UUID_I2C_CONFIG_GET)
        return self._config

    async def transaction(self, operation: Operation, address: int, read_len: int, write_data: bytes):
        if read_len > 240:
            ValueError("Maximum read length is 240 bytes")
        if address > 0x7F:
            ValueError("The I2C address should be in the range [0x01,0x7F]")
        b = bytearray([KONASHI_CFG_CMD_I2C, operation, read_len, address]) + bytearray(write_data)
        await self._write(KONASHI_UUID_CONTROL_CMD, b)
