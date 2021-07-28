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
KONASHI_CFG_CMD_SOFTPWM = 0x02
KONASHI_UUID_SOFTPWM_CONFIG_GET = "064d0203-8251-49d9-b6f3-f7ba35e5d0a1"

KONASHI_UUID_CONTROL_CMD = "064d0301-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_CTL_CMD_SOFTPWM = 0x02
KONASHI_UUID_SOFTPWM_OUTPUT_GET = "064d0304-8251-49d9-b6f3-f7ba35e5d0a1"


KONASHI_SOFTPWM_COUNT = 4
KONASHI_SOFTPWM_PIN_TO_GPIO_NUM = [4, 5, 6, 7]
class ControlType(IntEnum):
    DISABLED = 0
    DUTY = 1
    PERIOD = 2
class PinConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('control_type', c_uint8, 4),
        ('', c_uint8, 4),
        ('fixed_value', c_uint16)
    ]
    def __init__(self, control_type: ControlType, fixed_value: int=0):
        """
        control_type (ControlType): the control type for the pin
        fixed_value (int): the fixed value:
            if control_type is DUTY, this is the fixed period in units of 1ms (valid range: [0,65535])
            if control_type is PERIOD, this is the fixed duty cycle in units of 0.1% (valid range: [0,1000])
        """
        self.control_type = int(control_type)
        if control_type == ControlType.DUTY:
            if fixed_value < 0 or fixed_value > 65535:
                raise ValueError("The valid range for the fixed period is [0,65535] (unit: 1ms)")
        elif control_type == ControlType.PERIOD:
            if fixed_value < 0 or fixed_value > 1000:
                raise ValueError("The valid range for the fixed duty cycle is [0,1000] (unit: 0.1%)")
        self.fixed_value = fixed_value
    def __str__(self):
        s = "KonashiSoftPWMPinConfig("
        s += "DUTY control" if self.control_type==ControlType.DUTY else "PERIOD control" if self.control_type==ControlType.PERIOD else "DISABLED"
        if self.control_type != ControlType.DISABLED:
            s += ", "
            s += str(self.fixed_value*0.1)
            if self.control_type == ControlType.DUTY:
                s += "ms fixed period"
            else:
                s += r"% fixed duty cycle"
        s += ")"
        return s
_PinsConfig = PinConfig*KONASHI_SOFTPWM_COUNT

class PinControl(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('control_value', c_uint16),
        ('transition_duration', c_uint32)
    ]
    def __init__(self, control_value: int, transition_duration: int=0):
        """
        control_value (int): the control value to apply to the pin:
            if control_type is DUTY, this is the duty cycle control value in units of 0.1% (valid range: [0,1000])
            if control_type is PERIOD, this is the period control value in units of 1ms (valid range: [0,65535])
        transition_duration (int): duration to reach the target value in untis of 1ms (valid range: [0,4294967295])
        """
        if control_value < 0 or control_value > 65535:
            raise ValueError("The valid range for the control value is [0,65535]")
        if transition_duration < 0 or transition_duration > 4294967295:
            raise ValueError("The valid range for the transition duration is [0,4294967295] (unit: 1ms)")
        self.control_value = control_value
        self.transition_duration = transition_duration
        self.control_type = None
    def __str__(self):
        s = "KonashiSoftPWMPinControl("
        if self.control_type is None:
            s += "Control value "+str(self.control_value)+" raw, Transition duration "+str(self.transition_duration)+"ms"
        else:
            if self.control_type == ControlType.DISABLED:
                s += "DISABLED"
            else:
                s += int(self.control_value*0.1)
                if self.control_type == ControlType.PERIOD:
                    s += "ms period"
                else:
                    s += r"% duty cycle"
                s += ", Transition duration "+str(self.transition_duration)+"ms"
        s += ")"
        return s
_PinsControl = PinControl*KONASHI_SOFTPWM_COUNT


class SoftPWM(KonashiElementBase._KonashiElementBase):
    def __init__(self, konashi, gpio) -> None:
        super().__init__(konashi)
        self._gpio = gpio
        self._config = _PinsConfig()
        self._output = _PinsControl()
        self._trans_end_cb = None
        self._ongoing_control = []

    def __str__(self):
        return f'KonashiSoftPWM'

    def __repr__(self):
        return f'KonashiSoftPWM()'


    async def _on_connect(self) -> None:
        await self._enable_notify(KONASHI_UUID_SOFTPWM_CONFIG_GET, self._ntf_cb_config)
        await self._read(KONASHI_UUID_SOFTPWM_CONFIG_GET)
        await self._enable_notify(KONASHI_UUID_SOFTPWM_OUTPUT_GET, self._ntf_cb_output)
        await self._read(KONASHI_UUID_SOFTPWM_OUTPUT_GET)


    def _ntf_cb_config(self, sender, data):
        self._config = _PinsConfig.from_buffer_copy(data)

    def _ntf_cb_output(self, sender, data):
        self._output = _PinsControl.from_buffer_copy(data)
        for i in range(KONASHI_SOFTPWM_COUNT):
            if i in self._ongoing_control and self._output[i].transition_duration == 0:
                self._ongoing_control.remove(i)
                self._trans_end_cb(i)


    async def config_pins(self, configs: Sequence(Tuple[int, PinConfig])) -> None:
        """
        Specify a list of configurations in the format (pin_bitmask, config) with:
          pin_bitmask (int): a bitmask of the pins to apply this configuration to
          config (PinConfig): the configuration for the specified pins
        """
        b = bytearray([KONASHI_CFG_CMD_SOFTPWM])
        for config in configs:
            for i in range(KONASHI_SOFTPWM_COUNT):
                if (config[0]&(1<<i)) > 0:
                    if self._gpio._config[KONASHI_SOFTPWM_PIN_TO_GPIO_NUM[i]].function != int(Gpio.PinFunction.DISABLED) and self._gpio._config[KONASHI_SOFTPWM_PIN_TO_GPIO_NUM[i]].function != int(Gpio.PinFunction.PWM):
                        raise PinUnavailableError(f'Pin {KONASHI_SOFTPWM_PIN_TO_GPIO_NUM[i]} is already configured as {Gpio.KONASHI_GPIO_FUNCTION_STR[self._gpio._config[KONASHI_SOFTPWM_PIN_TO_GPIO_NUM[i]].function]}')
                    b.extend(bytearray([(i<<4)|(bytes(config[1])[0])]) + bytearray(config[1])[1:3])
        await self._write(KONASHI_UUID_CONFIG_CMD, b)

    async def get_pins_config(self, pin_bitmask: int) -> List[PinConfig]:
        """
        Get a list of current SoftPWM configurations for the pins specified in the bitmask.
        """
        await self._read(KONASHI_UUID_SOFTPWM_CONFIG_GET)
        l = []
        for i in range(KONASHI_SOFTPWM_COUNT):
            if (pin_bitmask&(1<<i)) > 0:
                l.append(self._config[i])
        return l

    def set_transition_end_cb(self, notify_callback: Callable[[int], None]) -> None:
        """
        The callback is called with parameters:
          pin (int)
        """
        self._trans_end_cb = notify_callback

    async def control_pins(self, controls: Sequence(Tuple[int, PinControl])) -> None:
        """
        Specify a list of controls in the format (pin, control) with:
          pin (int): a bitmask of the pins to apply this control to
          control (PinControl): the control for the specified pins
        """
        ongoing_control = []
        b = bytearray([KONASHI_CTL_CMD_SOFTPWM])
        for control in controls:
            for i in range(KONASHI_SOFTPWM_COUNT):
                if (control[0]&(1<<i)) > 0:
                    if self._gpio._config[KONASHI_SOFTPWM_PIN_TO_GPIO_NUM[i]].function != int(Gpio.PinFunction.PWM):
                        raise PinUnavailableError(f'Pin {KONASHI_SOFTPWM_PIN_TO_GPIO_NUM[i]} is not configured as PWM (configured as {Gpio.KONASHI_GPIO_FUNCTION_STR[self._gpio._config[KONASHI_SOFTPWM_PIN_TO_GPIO_NUM[i]].function]})')
                    if self._config[i].control_type == int(ControlType.DUTY):
                        if control[1].control_value < 0 or control[1].control_value > 1000:
                            raise ValueError("The valid range for the duty cycle control is [0,1000] (unit: 0.1%)")
                    elif self._config[i].control_type == int(ControlType.PERIOD):
                        if control[1].control_value < 0 or control[1].control_value > 65535:
                            raise ValueError("The valid range for the period control is [0,65535] (unit: 1ms)")
                    else:
                        raise PinUnavailableError(f'SoftPWM{i} is not enabled')
                    b.extend(bytearray([i])+bytearray(control[1]))
                    ongoing_control.append(i)
        await self._write(KONASHI_UUID_CONTROL_CMD, b)
        for i in ongoing_control:
            if i not in self._ongoing_control:
                self._ongoing_control.append(i)

    async def get_pins_control(self, pin_bitmask: int) -> List[PinControl]:
        """
        Get a list of current SoftPWM output control for the pins specified in the bitmask.
        """
        await self._ble_client.read_gatt_char(KONASHI_UUID_SOFTPWM_OUTPUT_GET)
        l = []
        for i in range(KONASHI_SOFTPWM_COUNT):
            if (pin_bitmask&(1<<i)) > 0:
                ctrl = self._output[i]
                ctrl.control_type = self._config[i].control_type
                l.append(ctrl)
        return l