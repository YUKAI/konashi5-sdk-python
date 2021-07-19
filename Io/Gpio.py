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


KONASHI_UUID_CONFIG_CMD = "064d0201-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_CFG_CMD_GPIO = 0x01
KONASHI_UUID_GPIO_CONFIG_GET = "064d0202-8251-49d9-b6f3-f7ba35e5d0a1"

KONASHI_UUID_CONTROL_CMD = "064d0301-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_CTL_CMD_GPIO= 0x01
KONASHI_UUID_GPIO_OUTPUT_GET = "064d0302-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_GPIO_INPUT = "064d0303-8251-49d9-b6f3-f7ba35e5d0a1"


KONASHI_GPIO_COUNT = 8
_KONASHI_GPIO_FUNCTION_STR = ["DISABLED", "GPIO", "PWM", "I2C", "SPI"]
class PinFunction(IntEnum):
    DISABLED = 0
    GPIO = 1
    PWM = 2
    I2C = 3
    SPI = 4
    def __int__(self):
        return self.value
class PinDirection(IntEnum):
    INPUT = 0
    OUTPUT = 1
    def __int__(self):
        return self.value
class PinWiredFunction(IntEnum):
    DISABLED = 0
    OPEN_DRAIN = 1
    OPEN_SOURCE = 2
    def __int__(self):
        return self.value
class PinConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('function', c_uint8, 4),
        ('', c_uint8, 4),
        ('pull_down', c_uint8, 1),
        ('pull_up', c_uint8, 1),
        ('wired_fct', c_uint8, 2),
        ('direction', c_uint8, 1),
        ('send_on_change', c_uint8, 1),
        ('', c_uint8, 2)
    ]
    def __init__(self, direction: PinDirection=PinDirection.INPUT, send_on_change: bool=True, pull_down: bool=False, pull_up: bool=False, wired_fct: PinWiredFunction=PinWiredFunction.DISABLED):
        """
        direction (PinDirection): the pin direction
        send_on_change (bool): if true, a notification is sent on pin level change
        pull_down (bool): if true, activate the pull down resistor
        pull_up (bool): if true, activate the pull up resistor
        wired_function (PinWiredFunction): use the pin in a wired function mode
        """
        self.direction = direction
        self.send_on_change = send_on_change
        self.pull_down = pull_down
        self.pull_up = pull_up
        self.wired_fct = wired_fct
    def __str__(self):
        s = "KonashiGpioPinConfig("
        try:
            s += _KONASHI_GPIO_FUNCTION_STR[self.function]
            if self.function == PinFunction.GPIO:
                s += ", "
                s += "OD" if self.wired_fct==PinWiredFunction.OPEN_DRAIN else "OS" if self.wired_fct==PinWiredFunction.OPEN_SOURCE else "OUT" if self.direction==PinDirection.OUTPUT else "IN"
                if self.pull_down:
                    s += ", PDOWN"
                if self.pull_up:
                    s += ", PUP"
                if self.send_on_change:
                    s += ", NTFY"
        except:
            s += ", Unknown"
        s += ")"
        return s
_PinsConfig = PinConfig*KONASHI_GPIO_COUNT

class PinControl(Enum):
    LOW = 0
    HIGH = 1
    TOGGLE = 2
    def __int__(self):
        return self.value
class PinLevel(Enum):
    LOW = 0
    HIGH = 1
    INVALID = 2
    def __int__(self):
        return self.value
class _PinIO(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('level', c_uint8, 1),
        ('', c_uint8, 3),
        ('valid', c_uint8, 1),
        ('', c_uint8, 3)
    ]
_PinsIO = _PinIO*KONASHI_GPIO_COUNT


class Gpio(KonashiElementBase._KonashiElementBase):
    def __init__(self, konashi) -> None:
        super().__init__(konashi)
        self._config = _PinsConfig()
        self._output = _PinsIO()
        self._input = _PinsIO()
        self._input_cb = None

    def __str__(self):
        return f'KonashiGpio'

    def __repr__(self):
        return f'KonashiGpio()'


    async def _on_connect(self) -> None:
        await self._enable_notify(KONASHI_UUID_GPIO_CONFIG_GET, self._ntf_cb_config)
        await self._read(KONASHI_UUID_GPIO_CONFIG_GET)
        await self._enable_notify(KONASHI_UUID_GPIO_OUTPUT_GET, self._ntf_cb_output)
        await self._read(KONASHI_UUID_GPIO_OUTPUT_GET)
        await self._enable_notify(KONASHI_UUID_GPIO_INPUT, self._ntf_cb_input)
        await self._read(KONASHI_UUID_GPIO_INPUT)
        

    def _ntf_cb_config(self, sender, data):
        self._config = _PinsConfig.from_buffer_copy(data)

    def _ntf_cb_output(self, sender, data):
        self._output = _PinsIO.from_buffer_copy(data)

    def _ntf_cb_input(self, sender, data):
        for i in range(KONASHI_GPIO_COUNT):
            if data[i]&0x10:
                val = data[i]&0x01
                if self._input[i].level != val:
                    if self._input_cb is not None:
                        self._input_cb(i, val)
        self._input = _PinsIO.from_buffer_copy(data)


    async def config_pins(self, configs: Sequence(Tuple[int, bool, PinConfig])) -> None:
        """
        Specify a list of configurations in the format (pin_bitmask, enable, config) with:
          pin_bitmask (int): a bitmask of the pins to apply this configuration to
          enable (bool): enable or disable the specified pins
          config (PinConfig): the configuration for the specified pins
        """
        b = bytearray([KONASHI_CFG_CMD_GPIO])
        for config in configs:
            for i in range(KONASHI_GPIO_COUNT):
                if (config[0]&(1<<i)) > 0:
                    if PinFunction(self._config[i].function) != PinFunction.DISABLED and PinFunction(self._config[i].function) != PinFunction.GPIO:
                        raise PinUnavailableError(f'Pin {i} is already configured as {_KONASHI_GPIO_FUNCTION_STR[self._config[i].function]}')
                    b.extend(bytearray([(i<<4)|(0x1 if config[1] else 0x0), bytes(config[2])[1]]))
        await self._write(KONASHI_UUID_CONFIG_CMD, b)

    async def get_pins_config(self, pin_bitmask: int) -> List[PinConfig]:
        """
        Get a list of current GPIO configurations for the pins specified in the bitmask.
        """
        await self._read(KONASHI_UUID_GPIO_CONFIG_GET)
        l = []
        for i in range(KONASHI_GPIO_COUNT):
            if (pin_bitmask&(1<<i)) > 0:
                l.append(self._config[i])
        return l

    def set_input_cb(self, notify_callback: Callable[[int, int], None]) -> None:
        """
        The callback is called with parameters:
          pin (int)
          value (int)
        """
        self._input_cb = notify_callback

    async def control_pins(self, controls: Sequence(Tuple[int, PinControl])) -> None:
        """
        Specify a list of controls in the format (pin, control) with:
          pin (int): a bitmask of the pins to apply this control to
          control (PinControl): the control for the specified pins
        """
        b = bytearray([KONASHI_CTL_CMD_GPIO])
        for control in controls:
            for i in range(KONASHI_GPIO_COUNT):
                if (control[0]&(1<<i)) > 0:
                    if PinFunction(self._config[i].function) != PinFunction.GPIO:
                        raise PinUnavailableError(f'Pin {i} is not configured as GPIO (configured as {_KONASHI_GPIO_FUNCTION_STR[self._config[i].function]})')
                    b.extend(bytearray([(i<<4)|(control[1])]))
        await self._write(KONASHI_UUID_CONFIG_CMD, b)

    async def get_pins_control(self, pin_bitmask: int) -> List[PinLevel]:
        """
        Get a list of current GPIO output levels for the pins specified in the bitmask.
        """
        await self._read(KONASHI_UUID_GPIO_OUTPUT_GET)
        l = []
        for i in range(KONASHI_GPIO_COUNT):
            if (pin_bitmask&(1<<i)) > 0:
                if not self._output[i].valid:
                    l.append(PinLevel.INVALID)
                else:
                    l.append(PinLevel(self._output[i].level))
        return l

    async def read_pins(self, pin_bitmask: int) -> List[PinLevel]:
        """
        Get a list of current GPIO input levels for the pins specified in the bitmask.
        """
        await self._read(KONASHI_UUID_GPIO_INPUT)
        l = []
        for i in range(KONASHI_GPIO_COUNT):
            if (pin_bitmask&(1<<i)) > 0:
                if not self._input[i].valid:
                    l.append(PinLevel.INVALID)
                else:
                    l.append(PinLevel(self._input[i].level))
        return l
