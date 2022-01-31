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


logger = logging.getLogger(__name__)


KONASHI_UUID_CONFIG_CMD = "064d0201-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_CFG_CMD_UART = 0x06
KONASHI_UUID_UART_CONFIG_GET = "064d0207-8251-49d9-b6f3-f7ba35e5d0a1"

KONASHI_UUID_CONTROL_CMD = "064d0301-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_CTL_CMD_UART_DATA = 0x06
KONASHI_UUID_UART_DATA_IN = "064d0309-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_UART_DATA_SEND_DONE = "064d030a-8251-49d9-b6f3-f7ba35e5d0a1"


class UARTParity(IntEnum):
    NONE = 0
    ODD = 1
    EVEN = 2
class UARTStopBits(IntEnum):
    HALF = 0
    ONE = 1
    ONEANDAHALF = 2
    TWO = 3
class UARTConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('stop_bits', c_uint8, 2),
        ('parity', c_uint8, 2),
        ('', c_uint8, 3),
        ('enabled', c_uint8, 1),
        ('baudrate', c_uint32)
    ]
    def __init__(self, enable: bool, baudrate: int=0, parity: UARTParity=UARTParity.NONE, stop_bits: UARTStopBits=UARTStopBits.ONE) -> None:
        """UART configuration.
        When enabling, please always spcify the baudrate, parity and stop bits. When disabling, they can be left as default.

        Args:
            enable (bool): True to enable, False to disable.
            baudrate (int, optional): The UART baudrate. Defaults to 0.
            parity (UARTParity, optional): The UART parity. Defaults to UARTParity.NONE.
            stop_bits (UARTStopBits, optional): The UART number of stop bits. Defaults to UARTStopBits.ONE.
        """
        self.enabled = enable
        self.baudrate = baudrate
        self.parity = parity
        self.stop_bits = stop_bits
    def __str__(self):
        s = "KonashiUARTConfig("
        if self.enabled:
            s += "enabled"
        else:
            s += "disabled"
        s += ", "+str(self.baudrate)
        if self.parity == UARTParity.NONE:
            s += ", No parity"
        elif self.parity == UARTParity.ODD:
            s += ", Odd parity"
        elif self.parity == UARTParity.EVEN:
            s += ", Even parity"
        if self.stop_bits == UARTStopBits.HALF:
            s += ", 0.5 stop bits"
        elif self.stop_bits == UARTStopBits.ONE:
            s += ", 1 stop bit"
        elif self.stop_bits == UARTStopBits.ONEANDAHALF:
            s += ", 1.5 stop bits"
        elif self.stop_bits == UARTStopBits.TWO:
            s += ", 2 stop bits"
        s += ")"
        return s


class _UART(KonashiElementBase._KonashiElementBase):
    def __init__(self, konashi) -> None:
        super().__init__(konashi)
        self._config = UARTConfig(False, 0, UARTParity.NONE, UARTStopBits.ONE)
        self._async_loop = None
        self._send_done_future = None
        self._data_in_cb = None

    def __str__(self):
        return f'KonashiUART'

    def __repr__(self):
        return f'KonashiUART()'


    async def _on_connect(self) -> None:
        await self._enable_notify(KONASHI_UUID_UART_CONFIG_GET, self._ntf_cb_config)
        await self._read(KONASHI_UUID_UART_CONFIG_GET)
        await self._enable_notify(KONASHI_UUID_UART_DATA_IN, self._ntf_cb_data_in)
        await self._enable_notify(KONASHI_UUID_UART_DATA_SEND_DONE, self._ntf_cb_send_done)


    def _ntf_cb_config(self, sender, data):
        logger.debug("Received config data: {}".format("".join("{:02x}".format(x) for x in data)))
        self._config = UARTConfig.from_buffer_copy(data)

    def _ntf_cb_data_in(self, sender, data):
        logger.debug("Received input data: {}".format("".join("{:02x}".format(x) for x in data)))
        if self._data_in_cb is not None:
            self._data_in_cb(data)

    def _ntf_cb_send_done(self, sender, data):
        logger.debug("Received send done data: {}".format("".join("{:02x}".format(x) for x in data)))
        if self._async_loop is not None and self._send_done_future is not None:
            self._async_loop.call_soon_threadsafe(self._send_done_future.set_result, data)


    async def config(self, config: UARTConfig) -> None:
        """Configure the UART peripheral.

        Args:
            config (UARTConfig): The configuration.
        """
        b = bytearray([KONASHI_CFG_CMD_UART]) + bytearray(config)
        await self._write(KONASHI_UUID_CONFIG_CMD, b)

    async def get_config(self) -> UARTConfig:
        """Get the current UART configuration.

        Returns:
            UARTConfig: The UART configuration.
        """
        await self._read(KONASHI_UUID_UART_CONFIG_GET)
        return self._config

    def set_data_in_cb(self, callback: Callable[[bytes], None]) -> None:
        """Set a callback for received UART data.

        Args:
            callback (Callable[[bytes], None]): The callback.
                The function takes 1 parameter and return nothing:
                    bytes: The received data. 
        """
        self._data_in_cb = callback

    async def send(self, write_data: bytes) -> bool:
        """Send UART data.

        Args:
            write_data (bytes): The data to send (length range is [1,127]).

        Raises:
            ValueError: The write data length is out of range.

        Returns:
            bool: True if successful, False otherwise.
        """
        if len(write_data) == 0:
            raise ValueError("Write data buffer cannot be empty")
        if len(write_data) > 127:
            raise ValueError("Maximum write data length is 127 bytes")
        b = bytearray([KONASHI_CTL_CMD_UART_DATA]) + bytearray(write_data)
        self._async_loop = asyncio.get_event_loop()
        self._send_done_future = self._async_loop.create_future()
        await self._write(KONASHI_UUID_CONTROL_CMD, b)
        res = await self._send_done_future
        self._async_loop = None
        self._send_done_future = None
        if len(res) == 1 and res[0] == 0x01:
            return True
        else:
            return False
