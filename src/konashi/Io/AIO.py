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
KONASHI_CFG_CMD_ANALOG = 0x04
KONASHI_UUID_ANALOG_CONFIG_GET = "064d0205-8251-49d9-b6f3-f7ba35e5d0a1"

KONASHI_UUID_CONTROL_CMD = "064d0301-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_CTL_CMD_ANALOG = 0x04
KONASHI_UUID_ANALOG_OUTPUT_GET = "064d0306-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_ANALOG_INPUT = "064d0307-8251-49d9-b6f3-f7ba35e5d0a1"


KONASHI_AIO_COUNT = 3
class ADCRef(IntEnum):
    DISABLE = 0
    REF_1V25 = 0x0+1
    REF_2V5 = 0x1+1
    REF_VDD = 0x2+1
class VDACRef(IntEnum):
    DISABLE = 0
    REF_1V25LN = 0x0+1
    REF_2V5LN = 0x1+1
    REF_1V25 = 0x2+1
    REF_2V5 = 0x3+1
    REF_VDD = 0x4+1
class IDACRange(IntEnum):
    DISABLE = 0
    RANGE0 = 0x0+1  # 0.05~1.6uA range, 50nA step
    RANGE1 = 0x1+1  # 1.6~4.7uA range, 100nA step
    RANGE2 = 0x2+1  # 0.5~16uA range, 500nA step
    RANGE3 = 0x3+1  # 2~64uA range, 2000nA step
class AIOPinDirection(IntEnum):
    INPUT = 0
    OUTPUT = 1
class AIOPinConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('direction', c_uint8, 1),
        ('send_on_change', c_uint8, 1),
        ('', c_uint8, 1),
        ('enabled', c_uint8, 1),
        ('', c_uint8, 4)
    ]
    def __init__(self, enabled: bool, direction: AIOPinDirection=AIOPinDirection.INPUT, send_on_change: bool=True):
        """AIO pin configuration.

        Args:
            enabled (bool): True to enable, False to disable.
            direction (AIOPinDirection, optional): The pin direction. Defaults to AIOPinDirection.INPUT.
            send_on_change (bool, optional): Unused, can be left as default. Defaults to True.
        """
        self.enabled = enabled
        self.send_on_change = send_on_change
        self.direction = direction
class _AIOConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('adc_update_period', c_uint8),
        ('adc_voltage_reference', c_uint8, 4),
        ('', c_uint8, 4),
        ('vdac_voltage_reference', c_uint8, 4),
        ('', c_uint8, 4),
        ('idac_current_step', c_uint8, 4),
        ('', c_uint8, 4)
    ]
class _AIOAllConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('pin', AIOPinConfig*KONASHI_AIO_COUNT),
        ('analog', _AIOConfig),
    ]

class AIOPinControl(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('control_value', c_uint16),
        ('transition_duration', c_uint32)
    ]
    def __init__(self, control_value: int, transition_duration: int=0):
        """AIO pin control.

        Args:
            control_value (int): The output control value. The valid range is [0,65535].
            transition_duration (int, optional): The output value transition duration in milliseconds. The valid range is [0,4294967295]. Defaults to 0.

        Raises:
            ValueError: The control value or transition duration is out of range.1
        """
        if control_value < 0 or control_value > 65535:
            raise ValueError("The valid range for the control value is [0,65535]")
        if transition_duration < 0 or transition_duration > 4294967295:
            raise ValueError("The valid range for the transition duration is [0,4294967295] (unit: 1ms)")
        self.control_value = control_value
        self.transition_duration = transition_duration
    def __str__(self):
        s = "KonashiAIOPinControl("
        if self.control_type is None:
            s += "Control value "+str(self.control_value)+", Transition duration "+str(self.transition_duration)+"ms"
        s += ")"
        return s
class _AIOPinOut(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('valid', c_uint8),
        ('control', AIOPinControl)
    ]
class _AIOPinsOut(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('idac_current_step', c_uint8, 4),
        ('vdac_voltage_reference', c_uint8, 4),
        ('pin', _AIOPinOut*KONASHI_AIO_COUNT)
    ]
class _AIOPinIn(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('valid', c_uint8),
        ('value', c_uint16)
    ]
class _AIOPinsIn(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('adc_voltage_reference', c_uint8, 4),
        ('', c_uint8, 4),
        ('pin', _AIOPinIn*KONASHI_AIO_COUNT)
    ]


class _AIO(KonashiElementBase._KonashiElementBase):
    def __init__(self, konashi) -> None:
        super().__init__(konashi)
        self._config = _AIOAllConfig()
        self._output = _AIOPinsOut()
        self._input = _AIOPinsIn()
        self._input_cb = None

    def __str__(self):
        return f'KonashiAIO'

    def __repr__(self):
        return f'KonashiAIO()'


    async def _on_connect(self) -> None:
        await self._enable_notify(KONASHI_UUID_ANALOG_CONFIG_GET, self._ntf_cb_config)
        await self._read(KONASHI_UUID_ANALOG_CONFIG_GET)
        await self._enable_notify(KONASHI_UUID_ANALOG_OUTPUT_GET, self._ntf_cb_output)
        await self._read(KONASHI_UUID_ANALOG_OUTPUT_GET)
        await self._enable_notify(KONASHI_UUID_ANALOG_INPUT, self._ntf_cb_input)
        await self._read(KONASHI_UUID_ANALOG_INPUT)
        

    def _ntf_cb_config(self, sender, data):
        logger.debug("Received config data: {}".format("".join("{:02x}".format(x) for x in data)))
        self._config = _AIOAllConfig.from_buffer_copy(data)

    def _ntf_cb_output(self, sender, data):
        logger.debug("Received output data: {}".format("".join("{:02x}".format(x) for x in data)))
        self._output = _AIOPinsOut.from_buffer_copy(data)

    def _ntf_cb_input(self, sender, data):
        logger.debug("Received input data: {}".format("".join("{:02x}".format(x) for x in data)))
        _new_input = _AIOPinsIn.from_buffer_copy(data)
        for i in range(KONASHI_AIO_COUNT):
            if _new_input.pin[i].valid:
                if _new_input.pin[i].value != self._input.pin[i].value:
                    if self._input_cb is not None:
                        self._input_cb(i, self._calc_voltage_for_value(_new_input.pin[i].value))
        self._input = _new_input


    def _calc_voltage_for_value(self, value: int) -> float:
        max_ref = None
        if self._config.analog.adc_voltage_reference == ADCRef.DISABLE:
            return None
        elif self._config.analog.adc_voltage_reference == ADCRef.REF_1V25:
            max_ref = 1.25
        elif self._config.analog.adc_voltage_reference == ADCRef.REF_2V5:
            max_ref = 2.5
        elif self._config.analog.adc_voltage_reference == ADCRef.REF_VDD:
            max_ref = 3.3
        else:
            return None
        return value*max_ref/65535

    async def config_adc_period(self, period: float) -> None:
        """Configure the ADC read period.
        The valid range is [0.1,25.6] seconds, in steps of 100ms.

        Args:
            period (float): The read period in seconds.

        Raises:
            ValueError: The period is out of range.
        """
        if period < 0.1 or period > 25.6:
            raise ValueError("Period should be in range [0.1,25.6] seconds")
        val = round(period*10)-1  # period = 100 * (val+1) in ms
        b = bytearray([KONASHI_CFG_CMD_ANALOG, 0xF0, int(val)&0xFF])
        await self._write(KONASHI_UUID_CONFIG_CMD, b)

    async def config_adc_ref(self, ref: ADCRef) -> None:
        """Configure the ADC voltage reference.

        Args:
            ref (ADCRef): The voltage reference.
        """
        b = bytearray([KONASHI_CFG_CMD_ANALOG, 0xE0|(ref&0x0F)])
        await self._write(KONASHI_UUID_CONFIG_CMD, b)

    async def config_vdac_ref(self, ref: VDACRef) -> None:
        """Configure the VDAC voltage reference.

        Args:
            ref (VDACRef): The voltage reference.
        """
        b = bytearray([KONASHI_CFG_CMD_ANALOG, 0xD0|(ref&0x0F)])
        await self._write(KONASHI_UUID_CONFIG_CMD, b)

    async def config_idac_range(self, range: IDACRange) -> None:
        """Configure the IDAC current range.

        Args:
            range (IDACRange): The current range.
        """
        b = bytearray([KONASHI_CFG_CMD_ANALOG, 0xC0|(range&0x0F)])
        await self._write(KONASHI_UUID_CONFIG_CMD, b)

    async def get_analog_config(self) -> _AIOConfig:
        """Get the analog configuration.
        This holds the configuration of the ADC, VDAC and IDAC.

        Returns:
            AIOConfig: The analog configuration.
                This class has 4 members:
                    adc_update_period: The ADC update period.
                    adc_voltage_reference: The ADC voltage reference.
                    vdac_voltage_reference: The VDAC voltage reference.
                    idac_current_step: The IDAC current step.
        """
        await self._read(KONASHI_UUID_ANALOG_CONFIG_GET)
        return self._config.analog

    async def config_pins(self, configs: Sequence(Tuple[int, AIOPinConfig])) -> None:
        """Configure analog pins.

        Args:
            configs (Sequence[Tuple[int, AIOPinConfig]]): The list of pin configurations.
                For each Tuple:
                    int: A bitmask of the pins to apply the configuration to.
                    AIOPinConfig: The configuration for the specified pins.
        """
        b = bytearray([KONASHI_CFG_CMD_ANALOG])
        for config in configs:
            for i in range(KONASHI_AIO_COUNT):
                if (config[0]&(1<<i)) > 0:
                    b.extend(bytearray([(i<<4)|(bytes(config[1])[0]&0x0F)]))
        await self._write(KONASHI_UUID_CONFIG_CMD, b)

    async def get_pins_config(self, pin_bitmask: int) -> List[AIOPinConfig]:
        """Get the configuration of the specified pins.

        Args:
            pin_bitmask (int): A bitmask of the pins to get the configuration for.

        Returns:
            List[AIOPinConfig]: The configurations of the specified pins.
        """
        await self._read(KONASHI_UUID_ANALOG_CONFIG_GET)
        l = []
        for i in range(KONASHI_AIO_COUNT):
            if (pin_bitmask&(1<<i)) > 0:
                l.append(self._config.pin[i])
        return l

    def set_input_cb(self, notify_callback: Callable[[int, int], None]) -> None:
        """Set an analog input callback function.

        Args:
            notify_callback (Callable[[int, int], None]): The callback function.
                The function takes 2 parameters and returns nothing:
                    int: The input pin number.
                    int: The pin input value.
        """
        self._input_cb = notify_callback

    async def control_pins(self, controls: Sequence(Tuple[int, AIOPinControl])) -> None:
        """Control analog pins.

        Args:
            controls (Sequence[Tuple[int, AIOPinControl]]): The list of pin controls.
                For each Tuple:
                    int: A bitmask of the pins to apply the control to.
                    AIOPinControl: The control for the specified pins.
        """
        b = bytearray([KONASHI_CTL_CMD_ANALOG])
        for control in controls:
            for i in range(KONASHI_AIO_COUNT):
                if (control[0]&(1<<i)) > 0:
                    b.extend(bytearray([i])+bytearray(control[1]))
        await self._write(KONASHI_UUID_CONTROL_CMD, b)

    def calc_control_value_for_voltage(self, voltage: float) -> int:
        """Calculate the control value for the wanted voltage.

        Args:
            voltage (float): The wanted voltage in Volts.

        Raises:
            KonashiDisabledError: The VDAC is disabled.
            KonashiInvalidError: The VDAC configuration is invalid.
            ValueError: The wanted voltage is out of range for the configuration.

        Returns:
            int: The corresponding control value.
        """
        max_ref = None
        if self._config.analog.vdac_voltage_reference == VDACRef.DISABLE:
            raise KonashiDisabledError("The VDAC is not enabled")
        elif self._config.analog.vdac_voltage_reference == VDACRef.REF_1V25LN or self._config.analog.vdac_voltage_reference == VDACRef.REF_1V25:
            max_ref = 1.25
        elif self._config.analog.vdac_voltage_reference == VDACRef.REF_2V5LN or self._config.analog.vdac_voltage_reference == VDACRef.REF_2V5:
            max_ref = 2.5
        elif self._config.analog.vdac_voltage_reference == VDACRef.REF_VDD:
            max_ref = 3.3
        else:
            raise KonashiInvalidError("The VDAC configuration is not valid")
        if voltage > max_ref:
            raise ValueError(f"The target voltage needs to be in the range [0,{max_ref}]")
        return round(voltage*4095/max_ref)

    def calc_control_value_for_current(self, current: float) -> int:
        """Calculate the control value for the wanted current.

        Args:
            current (float): The wanted current in Amperes.

        Raises:
            KonashiDisabledError: The IDAC is disabled.
            KonashiInvalidError: The IDAC configuration is invalid.
            ValueError: The wanted current is out of range for the configuration.

        Returns:
            int: The corresponding control value.
        """
        first = None
        last = None
        if self._config.analog.idac_current_step == IDACRange.DISABLE:
            raise KonashiDisabledError("The IDAC is not enabled")
        elif self._config.analog.idac_current_step == IDACRange.RANGE0:
            first = 0.05
            last = 1.6
        elif self._config.analog.idac_current_step == IDACRange.RANGE1:
            first = 1.6
            last = 4.7
        elif self._config.analog.idac_current_step == IDACRange.RANGE2:
            first = 0.5
            last = 16
        elif self._config.analog.idac_current_step == IDACRange.RANGE3:
            first = 2
            last = 64
        else:
            raise KonashiInvalidError("The IDAC configuration is not valid")
        if not first <= current <= last:
            raise ValueError(f"The target current needs to be in the range [{first},{last}]")
        return round((current-first)*31/(last-first))

    async def get_pins_control(self, pin_bitmask: int) -> List[AIOPinControl]:
        """Get the output control of the specified pins.

        Args:
            pin_bitmask (int): A bitmask of the pins to get the output control for.

        Returns:
            List[AIOPinControl]: The output control of the specified pins.
        """
        await self._read(KONASHI_UUID_ANALOG_OUTPUT_GET)
        l = []
        for i in range(KONASHI_AIO_COUNT):
            if (pin_bitmask&(1<<i)) > 0:
                if not self._output.pin[i].valid:
                    l.append(None)
                else:
                    l.append(self._output.pin[i].control)
        return l

    async def read_pins(self, pin_bitmask: int) -> List[int]:
        """Get the input value of the specified pins.

        Args:
            pin_bitmask (int): A bitmask of the pins to get the input value for.

        Returns:
            List[int]: The input value of the specified pins in Volts.
        """
        await self._read(KONASHI_UUID_ANALOG_INPUT)
        l = []
        for i in range(KONASHI_AIO_COUNT):
            if (pin_bitmask&(1<<i)) > 0:
                if not self._input.pin[i].valid:
                    l.append(None)
                else:
                    l.append(self._calc_voltage_for_value(self._input.pin[i].value))
        return l
