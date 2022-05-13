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
KONASHI_CFG_CMD_NEOPIXEL = 0x08
KONASHI_UUID_NEOPIXEL_CONFIG_GET = "064d0209-8251-49d9-b6f3-f7ba35e5d0a1"

KONASHI_UUID_CONTROL_CMD = "064d0301-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_CTL_CMD_NEOPIXEL_DATA = 0x08
KONASHI_UUID_NEOPIXEL_OUTPUT_GET = "064d030c-8251-49d9-b6f3-f7ba35e5d0a1"


KONASHI_NEOPIXEL_MAX_LED_COUNT = 16

KONASHI_NEOPIXEL_PIN_TO_GPIO_NUM = [0, 1]


class NeoPixelConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('count', c_uint8, 4),
        ('', c_uint8, 2),
        ('pin', c_uint8, 1),
        ('enabled', c_uint8, 1)
    ]
    def __init__(self, enable: bool, pin: int = 0, count: int = 0) -> None:
        """NeoPixel configuration.
        When enabling, please always specify the pin and LED count. When disabling, they can be left as default.

        Args:
            enable (bool): True to enable, False to disable.
            pin (int, optional): The NeoPixel pin (0 or 1).
            count (count, optional): The number of LEDs ([1,16]).
        """
        self.enabled = enable
        assert(pin == 0 or pin == 1)
        self.pin = pin
        assert((1 if enable else 0) <= count <= KONASHI_NEOPIXEL_MAX_LED_COUNT)
        self.count = count-1 if enable else 0
    def __str__(self):
        s = "KonashiNeoPixelConfig("
        if self.enabled:
            s += "enabled"
            s += ", pin NEOP{}".format(self.pin)
            s += ", {} LEDs".format(self.count+1)
        else:
            s += "disabled"
        s += ")"
        return s

class NeoPixelLedOutput(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('led', c_uint8, 4),
        ('used', c_uint8, 1),
        ('', c_uint8, 3),
        ('red', c_uint8),
        ('green', c_uint8),
        ('blue', c_uint8),
        ('transition_duration', c_uint32)
    ]
    def __init__(self, r: int, g: int, b: int, duration: int = 0):
        """NeoPixel LED control.

        Args:
            led (int): The LED number ([0,15]).
            r (int): The Red color component (valid range is [0,255], the value is truncated if out of range).
            g (int): The Green color component (valid range is [0,255], the value is truncated if out of range).
            b (int): The Blue color component (valid range is [0,255], the value is truncated if out of range).
            duration (int, optional): The color transition duration in milliseconds. The valid range is [0,4294967295]. Defaults to 0.

        Raises:
            ValueError: The control value or transition duration is out of range.1
        """
        self.red = r &0xFF
        self.green = g&0xFF
        self.blue = b&0xFF
        assert(0 <= duration <= 4294967295)
        self.transition_duration = duration
    def __str__(self):
        s = "KonashiNeoPixelLedControl("+")"
        return s
_LedsControl = NeoPixelLedOutput*KONASHI_NEOPIXEL_MAX_LED_COUNT


class _NeoPixel(KonashiElementBase._KonashiElementBase):
    def __init__(self, konashi, gpio) -> None:
        super().__init__(konashi)
        self._gpio = gpio
        self._config = NeoPixelConfig(False, 0, 0)
        self._output = _LedsControl()

    def __str__(self):
        return f'KonashiNeoPixel'

    def __repr__(self):
        return f'KonashiNeoPixel()'


    async def _on_connect(self) -> None:
        await self._enable_notify(KONASHI_UUID_NEOPIXEL_CONFIG_GET, self._ntf_cb_config)
        await self._read(KONASHI_UUID_NEOPIXEL_CONFIG_GET)
        await self._enable_notify(KONASHI_UUID_NEOPIXEL_OUTPUT_GET, self._ntf_cb_output)
        await self._read(KONASHI_UUID_NEOPIXEL_OUTPUT_GET)


    def _ntf_cb_config(self, sender, data):
        logger.debug("Received config data: {}".format("".join("{:02x}".format(x) for x in data)))
        self._config = NeoPixelConfig.from_buffer_copy(data)

    def _ntf_cb_output(self, sender, data):
        logger.debug("Received output data: {}".format("".join("{:02x}".format(x) for x in data)))
        self._output = _LedsControl.from_buffer_copy(data)


    async def config(self, config: NeoPixelConfig) -> None:
        """Configure the NeoPixel peripheral. 

        Args:
            config (NeoPixelConfig): The configuration.

        Raises:
            PinUnavailableError: At least one of the pins is already configured with another function.
        """
        if config.enabled:
            if self._gpio._config[KONASHI_NEOPIXEL_PIN_TO_GPIO_NUM[config.pin]].function != int(GPIO.GPIOPinFunction.DISABLED) and self._gpio._config[KONASHI_NEOPIXEL_PIN_TO_GPIO_NUM[config.pin]].function != int(GPIO.GPIOPinFunction.NEOPIXEL):
                raise PinUnavailableError(f'Pin {KONASHI_NEOPIXEL_PIN_TO_GPIO_NUM[config.pin]} is already configured as {GPIO._KONASHI_GPIO_FUNCTION_STR[self._gpio._config[KONASHI_NEOPIXEL_PIN_TO_GPIO_NUM[config.pin]].function]}')
        b = bytearray([KONASHI_CFG_CMD_NEOPIXEL]) + bytearray(config)
        await self._write(KONASHI_UUID_CONFIG_CMD, b)

    async def get_config(self) -> NeoPixelConfig:
        """Get the current NeoPixel configuration.

        Returns:
            NeoPixelConfig: The NeoPixel configuration.
        """
        await self._read(KONASHI_UUID_NEOPIXEL_CONFIG_GET)
        return self._config

    async def control_leds(self, controls: Sequence(Tuple[int, NeoPixelLedOutput])) -> None:
        """Control NeoPixel LEDs.

        Args:
            controls (Sequence[Tuple[int, NeoPixelLedOutput]]): The list of LED controls.
                For each Tuple:
                    int: The LED number to apply the control to.
                    AIOPinControl: The control for the specified LED.
        """
        b = bytearray([KONASHI_CTL_CMD_NEOPIXEL_DATA])
        for control in controls:
            led = control[0]
            assert(0 <= led <= (KONASHI_NEOPIXEL_MAX_LED_COUNT-1))
            assert(self._output[led].used == 1)
            ctrl = control[1]
            ctrl.led = led
            b.extend(bytearray(ctrl))
        await self._write(KONASHI_UUID_CONTROL_CMD, b)

    async def get_leds_control(self) -> List[NeoPixelLedOutput]:
        """Get the output control of the NeoPixel LEDs.

        Returns:
            List[NeoPixelLedOutput]: The output control of the NeoPixel LEDs.
        """
        await self._read(KONASHI_UUID_NEOPIXEL_OUTPUT_GET)
        l = []
        for i in range(KONASHI_NEOPIXEL_MAX_LED_COUNT):
            if self._output[i].used:
                l.append(self._output.pin[i])
        return l
