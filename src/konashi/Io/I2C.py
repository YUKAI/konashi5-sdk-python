#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import struct
import logging
from ctypes import *
from typing import *
from enum import *

from bleak import *

from .. import KonashiElementBase
from ..Errors import *
from . import GPIO


logger = logging.getLogger(__name__)


KONASHI_UUID_CONFIG_CMD = "064d0201-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_CFG_CMD_I2C = 0x05
KONASHI_UUID_I2C_CONFIG_GET = "064d0206-8251-49d9-b6f3-f7ba35e5d0a1"

KONASHI_UUID_CONTROL_CMD = "064d0301-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_CTL_CMD_I2C_DATA = 0x05
KONASHI_UUID_I2C_DATA_IN = "064d0308-8251-49d9-b6f3-f7ba35e5d0a1"


KONASHI_I2C_SDA_PINNB = 6
KONASHI_I2C_SCL_PINNB = 7
class I2CMode(IntEnum):
    STANDARD = 0
    FAST = 1
class I2CConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('mode', c_uint8, 1),
        ('enabled', c_uint8, 1),
        ('', c_uint8, 6)
    ]
    def __init__(self, enable: bool, mode: I2CMode) -> None:
        """I2C configuration.

        Args:
            enable (bool): True to enable, False to disable.
            mode (I2CMode): The I2C mode.
        """
        self.enabled = enable
        self.mode = mode
    def __str__(self):
        s = "KonashiI2CConfig("
        if self.enabled:
            s += "enabled"
        else:
            s += "disabled"
        s += ", mode:"
        if self.mode == I2CMode.STANDARD:
            s += "standard"
        elif self.mode == I2CMode.FAST:
            s += "fast"
        else:
            s += "unknown"
        s += ")"
        return s

class I2COperation(IntEnum):
    WRITE = 0
    READ = 1
    WRITE_READ = 2
class I2CResult(IntEnum):
    DONE = 0  # Transfer completed successfully.
    NACK = 1  # NACK received during transfer.
    BUS_ERR = 2  # Bus error during transfer (misplaced START/STOP).
    ARB_LOST = 3  # Arbitration lost during transfer.
    USAGE_FAULT = 4  # Usage fault.
    SW_FAULT = 5  # SW fault.


class _I2C(KonashiElementBase._KonashiElementBase):
    def __init__(self, konashi, gpio) -> None:
        super().__init__(konashi)
        self._gpio = gpio
        self._config = I2CConfig(False, I2CMode.STANDARD)
        self._async_loop = None
        self._data_in_future = None

    def __str__(self):
        return f'KonashiI2C'

    def __repr__(self):
        return f'KonashiI2C()'


    async def _on_connect(self) -> None:
        await self._enable_notify(KONASHI_UUID_I2C_CONFIG_GET, self._ntf_cb_config)
        await self._read(KONASHI_UUID_I2C_CONFIG_GET)
        await self._enable_notify(KONASHI_UUID_I2C_DATA_IN, self._ntf_cb_data_in)


    def _ntf_cb_config(self, sender, data):
        logger.debug("Received config data: {}".format("".join("{:02x}".format(x) for x in data)))
        self._config = I2CConfig.from_buffer_copy(data)

    def _ntf_cb_data_in(self, sender, data):
        logger.debug("Received input data: {}".format("".join("{:02x}".format(x) for x in data)))
        if self._async_loop is not None and self._data_in_future is not None:
            self._async_loop.call_soon_threadsafe(self._data_in_future.set_result, data)


    async def config(self, config: I2CConfig) -> None:
        """Configure I2C.

        Args:
            config (I2CConfig): The configuration.

        Raises:
            PinUnavailableError: One of the I2C pins is set to another function.
        """
        if config.enabled:
            if self._gpio._config[KONASHI_I2C_SDA_PINNB].function != int(GPIO.GPIOPinFunction.DISABLED) and self._gpio._config[KONASHI_I2C_SDA_PINNB].function != int(GPIO.GPIOPinFunction.I2C):
                raise PinUnavailableError(f'Pin {KONASHI_I2C_SDA_PINNB} is already configured as {GPIO._KONASHI_GPIO_FUNCTION_STR[self._gpio._config[KONASHI_I2C_SDA_PINNB].function]}')
            if self._gpio._config[KONASHI_I2C_SCL_PINNB].function != int(GPIO.GPIOPinFunction.DISABLED) and self._gpio._config[KONASHI_I2C_SCL_PINNB].function != int(GPIO.GPIOPinFunction.I2C):
                raise PinUnavailableError(f'Pin {KONASHI_I2C_SCL_PINNB} is already configured as {GPIO._KONASHI_GPIO_FUNCTION_STR[self._gpio._config[KONASHI_I2C_SCL_PINNB].function]}')
        b = bytearray([KONASHI_CFG_CMD_I2C]) + bytearray(config)
        await self._write(KONASHI_UUID_CONFIG_CMD, b)

    async def get_config(self) -> I2CConfig:
        """Get the current I2C configuration

        Returns:
            I2CConfig: The I2C configuration.
        """
        await self._read(KONASHI_UUID_I2C_CONFIG_GET)
        return self._config

    async def transaction(self, operation: I2COperation, address: int, read_len: int, write_data: bytes) -> Tuple[I2CResult, int, bytes]:
        """Perform an I2C transaction.

        Args:
            operation (I2COperation): The transaction operation.
            address (int): The I2C slave address (address range is 0x00 to 0x7F).
            read_len (int): The length of the data to read (0 to 126 bytes).
            write_data (bytes): The data to write (valid length 0 to 124 bytes).

        Returns:
            Tuple[I2CResult, int, bytes]: result, address, bytes.
                I2CResult: The transaction result.
                int: The transaction slave address.
                bytes: The read data (if there is no read data, the length will be 0).

        Raises:
            ValueError: The read length or slave address is out of range, or the write data is too long.
        """
        if read_len > 126:
            raise ValueError("Maximum read length is 126 bytes")
        if address > 0x7F:
            raise ValueError("The I2C address should be in the range [0x01,0x7F]")
        if len(write_data) > 124:
            raise ValueError("Maximum write data length is 124 bytes")
        b = bytearray([KONASHI_CTL_CMD_I2C_DATA, operation, read_len, address]) + bytearray(write_data)
        self._async_loop = asyncio.get_event_loop()
        self._data_in_future = self._async_loop.create_future()
        await self._write(KONASHI_UUID_CONTROL_CMD, b)
        res = await self._data_in_future
        self._async_loop = None
        self._data_in_future = None
        ret = (I2CResult(res[0]), res[1], res[2:])
        return ret
