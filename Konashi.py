#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import struct
from ctypes import *
from typing import *
from enum import *

from bleak import *


KONASHI_ADV_SERVICE_UUID = "064d0100-8251-49d9-b6f3-f7ba35e5d0a1"

KONASHI_UUID_CONFIG_CMD = "064d0201-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_CFG_CMD_GPIO = 0x01
KONASHI_CFG_CMD_SOFTPWM = 0x02
KONASHI_CFG_CMD_HARDPWM = 0x03
KONASHI_CFG_CMD_ANALOG = 0x04
KONASHI_CFG_CMD_I2C = 0x05
KONASHI_CFG_CMD_UART = 0x06
KONASHI_CFG_CMD_SPI = 0x07
KONASHI_UUID_GPIO_CONFIG_GET = "064d0202-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_SOFTPWM_CONFIG_GET = "064d0203-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_HARDPWM_CONFIG_GET = "064d0204-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_ANALOG_CONFIG_GET = "064d0205-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_I2C_CONFIG_GET = "064d0206-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_UART_CONFIG_GET = "064d0207-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_SPI_CONFIG_GET = "064d0208-8251-49d9-b6f3-f7ba35e5d0a1"

KONASHI_UUID_CONTROL_CMD = "064d0301-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_CTL_CMD_GPIO= 0x01
KONASHI_CTL_CMD_SOFTPWM = 0x02
KONASHI_CTL_CMD_HARDPWM = 0x03
KONASHI_CTL_CMD_ANALOG = 0x04
KONASHI_CTL_CMD_I2C_DATA = 0x05
KONASHI_CTL_CMD_UART_DATA = 0x06
KONASHI_CTL_CMD_SPI_DATA = 0x07
KONASHI_UUID_GPIO_OUTPUT_GET = "064d0302-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_GPIO_INPUT = "064d0303-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_SOFTPWM_OUTPUT_GET = "064d0304-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_HARDPWM_OUTPUT_GET = "064d0305-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_ANALOG_OUTPUT_GET = "064d0306-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_ANALOG_INPUT = "064d0307-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_I2C_DATA_IN = "064d0308-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_UART_DATA_IN = "064d0309-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_UART_DATA_SEND_DONE = "064d030a-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_SPI_DATA_IN = "064d030b-8251-49d9-b6f3-f7ba35e5d0a1"

KONASHI_UUID_BUILTIN = "064d0400-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_BUILTIN_TEMPERATURE = "00002a6e-0000-1000-8000-00805f9b34fb"
KONASHI_UUID_BUILTIN_HUMIDITY = "00002a6f-0000-1000-8000-00805f9b34fb"
KONASHI_UUID_BUILTIN_PRESSURE = "00002a6d-0000-1000-8000-00805f9b34fb"
KONASHI_UUID_BUILTIN_PRESENCE = "00002ae2-0000-1000-8000-00805f9b34fb"
KONASHI_UUID_BUILTIN_ACCELGYRO = "064d0401-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_BUILTIN_RGB_SET = "064d0402-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_BUILTIN_RGB_GET = "064d0403-8251-49d9-b6f3-f7ba35e5d0a1"


### GPIO
KONASHI_GPIO_COUNT = 8
KONASHI_GPIO_FUNCTION_STR = ["DISABLED", "GPIO", "PWM", "I2C", "SPI"]
class KonashiGpioPinFunction(Enum):
    DISABLED = 0
    GPIO = 1
    PWM = 2
    I2C = 3
    SPI = 4
    def __int__(self):
        return self.value
class KonashiGpioPinDirection(Enum):
    INPUT = 0
    OUTPUT = 1
    def __int__(self):
        return self.value
class KonashiGpioPinWiredFunction(Enum):
    DISABLED = 0
    OPEN_DRAIN = 1
    OPEN_SOURCE = 2
    def __int__(self):
        return self.value
class KonashiGpioPinConfig(LittleEndianStructure):
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
    def __init__(self, direction: KonashiGpioPinDirection=KonashiGpioPinDirection.INPUT, send_on_change: bool=True, pull_down: bool=False, pull_up: bool=False, wired_fct: KonashiGpioPinWiredFunction=KonashiGpioPinWiredFunction.DISABLED):
        """
        direction (KonashiGpioPinDirection): the pin direction
        send_on_change (bool): if true, a notification is sent on pin level change
        pull_down (bool): if true, activate the pull down resistor
        pull_up (bool): if true, activate the pull up resistor
        wired_function (KonashiGpioPinWiredFunction): use the pin in a wired function mode
        """
        self.direction = direction
        self.send_on_change = send_on_change
        self.pull_down = pull_down
        self.pull_up = pull_up
        self.wired_fct = wired_fct
    def __str__(self):
        s = "KonashiGpioPinConfig("
        try:
            s += KONASHI_GPIO_FUNCTION_STR[self.function]
            if self.function == KONASHI_GPIO_FUNCTION_GPIO:
                s += ", "
                s += "OD" if self.wired_fct==KonashiGpioPinWiredFunction.OPEN_DRAIN else "OS" if self.wired_fct==KonashiGpioPinWiredFunction.OPEN_SOURCE else "OUT" if self.direction==KonashiGpioPinDirection.OUTPUT else "IN"
                if self.pull_down:
                    s += ", PDOWN"
                if self.pull_up:
                    s += ", PUP"
                if self.send_on_change:
                    s += ", NTFY"
        except:
            s += "Unknown"
        s += ")"
        return s
_KonashiGpioPinsConfig = KonashiGpioPinConfig*KONASHI_GPIO_COUNT

class KonashiGpioPinControl(Enum):
    LOW = 0
    HIGH = 1
    TOGGLE = 2
    def __int__(self):
        return self.value
class KonashiGpioPinLevel(Enum):
    LOW = 0
    HIGH = 1
    INVALID = 2
    def __int__(self):
        return self.value
class _KonashiGpioPinIO(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('level', c_uint8, 1),
        ('', c_uint8, 3),
        ('valid', c_uint8, 1),
        ('', c_uint8, 3)
    ]
_KonashiGpioPinsIO = _KonashiGpioPinIO*KONASHI_GPIO_COUNT

class KonashiSoftPwmPinConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('control', c_uint8, 4),
        ('', c_uint8, 4),
        ('fixed_value', c_uint16)
    ]

KONASHI_HARDPWM_COUNT = 4
class KonashiHardPwmPinConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('enabled', c_uint8, 1),
        ('', c_uint8, 7)
    ]
class KonashiHardPwmConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('pin', KonashiHardPwmPinConfig*KONASHI_HARDPWM_COUNT),
        ('prescale', c_uint8, 4),
        ('clock', c_uint8, 4),
        ('period', c_uint16)
    ]

KONASHI_AIO_COUNT = 3
class KonashiAnalogPinConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('direction', c_uint8, 1),
        ('send_on_change', c_uint8, 1),
        ('', c_uint8, 1),
        ('enabled', c_uint8, 1),
        ('', c_uint8, 4)
    ]
class KonashiAnalogConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('pin', KonashiAnalogPinConfig*KONASHI_AIO_COUNT),
        ('adc_update_period', c_uint8),
        ('adc_voltage_reference', c_uint8, 4),
        ('', c_uint8, 4),
        ('vdac_voltage_reference', c_uint8, 4),
        ('', c_uint8, 4),
        ('idac_current_step', c_uint8, 4),
        ('', c_uint8, 4)
    ]

class KonashiI2cConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('mode', c_uint8, 1),
        ('enabled', c_uint8, 1),
        ('', c_uint8, 6)
    ]

class KonashiUartConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('stop_bits', c_uint8, 2),
        ('parity', c_uint8, 2),
        ('', c_uint8, 3),
        ('enabled', c_uint8, 1),
        ('baudrate', c_uint32)
    ]

class KonashiSpiConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('mode', c_uint8, 2),
        ('', c_uint8, 1),
        ('endian', c_uint8, 1),
        ('', c_uint8, 3),
        ('enabled', c_uint8, 1),
        ('bitrate', c_uint32)
    ]




class KonashiError(Exception):
    pass

class NotFoundError(Exception):
    pass

class InvalidDeviceError(Exception):
    pass

class PinInvalidError(Exception):
    pass

class PinUnavailableError(Exception):
    pass


class Konashi:
    def __init__(self, name: str) -> None:
        self._name = name
        self._ble_dev = None
        self._ble_client = None
        self._gpio_config = _KonashiGpioPinsConfig()
        self._gpio_output = _KonashiGpioPinsIO()
        self._gpio_input = _KonashiGpioPinsIO()
        self._gpio_input_cb = None
        self._builtin_temperature_cb = None
        self._builtin_humidity_cb = None
        self._builtin_pressure_cb = None
        self._builtin_presence_cb = None
        self._builtin_accelgyro_cb = None
        self._builtin_rgb_transition_end_cb = None

    def __str__(self):
        return f'Konashi {self._name} ({"Unknown" if self._ble_dev is None else self._ble_dev.address})'

    def __repr__(self):
        return f'Konashi(name="{self._name}")'

    def __eq__(self, other):
        if self._ble_dev is not None and other._ble_dev is not None:
            return self._ble_dev.address == other._ble_dev.address
        return self._name == other._name

    def __ne__(self, other):
        return not self.__eq__(other)
        

    @staticmethod
    async def find(name: str, timeout: float) -> Konashi:
        if not timeout > 0.0:
            raise ValueError("Timeout should be longer than 0 seconds")
        _konashi = None
        _invalid = False
        _scan_task = None
        _scanner = BleakScanner()
        def _scan_cb(dev: BLEDevice, adv: AdvertisementData):
            nonlocal _konashi
            nonlocal _invalid
            if dev.name == name:
                if KONASHI_ADV_SERVICE_UUID in adv.service_uuids:
                    _konashi = Konashi(name)
                    _konashi._ble_dev = dev
                else:
                    _invalid = True
                _scanner.register_detection_callback(None)
                if _scan_task:
                    _scan_task.cancel()
        _scanner.register_detection_callback(_scan_cb)
        _timedout = False
        async def _scan_coro(t: float) -> None:
            nonlocal _timedout
            try:
                await _scanner.start()
                if timeout > 0:
                    await asyncio.sleep(t)
                else:
                    while True:
                        await asyncio.sleep(100)
                _timedout = True
            except asyncio.CancelledError:
                _timedout = False
            finally:
                await _scanner.stop()
        _scan_task = asyncio.create_task(_scan_coro(timeout))
        await _scan_task
        if _timedout:
            raise NotFoundError(f'Could not find {name}')
        elif _invalid:
            raise InvalidDeviceError(f'{name} is not a Konashi device')
        else:
            return _konashi

    @staticmethod
    async def search(timeout: float) -> List[Konashi]:
        if not timeout > 0.0:
            raise ValueError("Timeout should be longer than 0 seconds")
        _konashi = []
        def _scan_cb(dev: BLEDevice, adv: AdvertisementData):
            nonlocal _konashi
            if KONASHI_ADV_SERVICE_UUID in adv.service_uuids:
                k = Konashi(dev.name)
                k._ble_dev = dev
                if k not in _konashi:
                    _konashi.append(k)
        _scanner = BleakScanner()
        _scanner.register_detection_callback(_scan_cb)
        await _scanner.start()
        await asyncio.sleep(timeout)
        _scanner.register_detection_callback(None)
        await _scanner.stop()
        return _konashi

    async def connect(self, timeout: float) -> None:
        if not timeout > 0.0:
            raise ValueError("Timeout should be longer than 0 seconds")
        if self._ble_dev is None:
            try:
                k = await self.find(self._name, timeout)
                self._ble_dev = k._ble_dev
            except NotFoundError:
                raise
            except InvalidDeviceError:
                raise
        if self._ble_client is None:
            self._ble_client = BleakClient(self._ble_dev.address)
        try:
            _con = await self._ble_client.connect(timeout=timeout)
        except BleakError as e:
            self._ble_client = None
            raise KonashiError(f'Error occured during BLE connect: "{str(e)}"')
        if _con:
            buf = await self._ble_client.read_gatt_char(KONASHI_UUID_GPIO_CONFIG_GET)
            self._gpio_config = _KonashiGpioPinsConfig.from_buffer_copy(buf)
            await self._ble_client.start_notify(KONASHI_UUID_GPIO_CONFIG_GET, self._ntf_cb_gpio_config_get)
            await self._ble_client.start_notify(KONASHI_UUID_SOFTPWM_CONFIG_GET, self._ntf_cb_softpwm_config_get)
            await self._ble_client.start_notify(KONASHI_UUID_HARDPWM_CONFIG_GET, self._ntf_cb_hardpwm_config_get)
            await self._ble_client.start_notify(KONASHI_UUID_ANALOG_CONFIG_GET, self._ntf_cb_analog_config_get)
            await self._ble_client.start_notify(KONASHI_UUID_I2C_CONFIG_GET, self._ntf_cb_i2c_config_get)
            await self._ble_client.start_notify(KONASHI_UUID_UART_CONFIG_GET, self._ntf_cb_uart_config_get)
            await self._ble_client.start_notify(KONASHI_UUID_SPI_CONFIG_GET, self._ntf_cb_spi_config_get)

            buf = await self._ble_client.read_gatt_char(KONASHI_UUID_GPIO_OUTPUT_GET)
            self._gpio_output = _KonashiGpioPinsIO.from_buffer_copy(buf)
            await self._ble_client.start_notify(KONASHI_UUID_GPIO_OUTPUT_GET, self._ntf_cb_gpio_output_get)
            buf = await self._ble_client.read_gatt_char(KONASHI_UUID_GPIO_INPUT)
            self._gpio_input = _KonashiGpioPinsIO.from_buffer_copy(buf)
            await self._ble_client.start_notify(KONASHI_UUID_GPIO_INPUT, self._ntf_cb_gpio_input)
            await self._ble_client.start_notify(KONASHI_UUID_SOFTPWM_OUTPUT_GET, self._ntf_cb_softpwm_output_get)
            await self._ble_client.start_notify(KONASHI_UUID_HARDPWM_OUTPUT_GET, self._ntf_cb_hardpwm_output_get)
            await self._ble_client.start_notify(KONASHI_UUID_ANALOG_OUTPUT_GET, self._ntf_cb_analog_output_get)
            await self._ble_client.start_notify(KONASHI_UUID_ANALOG_INPUT, self._ntf_cb_analog_input)
            await self._ble_client.start_notify(KONASHI_UUID_I2C_DATA_IN, self._ntf_cb_i2c_data_in)
            await self._ble_client.start_notify(KONASHI_UUID_UART_DATA_IN, self._ntf_cb_uart_data_in)
            await self._ble_client.start_notify(KONASHI_UUID_UART_DATA_SEND_DONE, self._ntf_cb_uart_data_send_done)
            await self._ble_client.start_notify(KONASHI_UUID_SPI_DATA_IN, self._ntf_cb_spi_data_in)

            has_builtin = False
            srvcs = await self._ble_client.get_services()
            for s in srvcs:
                if s.uuid == KONASHI_UUID_BUILTIN:
                    has_builtin = True
            if has_builtin:
                print("Konashi has built-in sensors")
                await self._ble_client.start_notify(KONASHI_UUID_BUILTIN_RGB_GET, self._ntf_cb_builtin_rgb_get)

    async def disconnect(self) -> None:
        if self._ble_client is not None:
            await self._ble_client.disconnect()
            self._ble_client = None


    def _ntf_cb_gpio_config_get(self, sender, data):
        self._gpio_config = _KonashiGpioPinsConfig.from_buffer_copy(data)
    def _ntf_cb_softpwm_config_get(self, sender, data):
        pass
    def _ntf_cb_hardpwm_config_get(self, sender, data):
        pass
    def _ntf_cb_analog_config_get(self, sender, data):
        pass
    def _ntf_cb_i2c_config_get(self, sender, data):
        pass
    def _ntf_cb_uart_config_get(self, sender, data):
        pass
    def _ntf_cb_spi_config_get(self, sender, data):
        pass

    def _ntf_cb_gpio_output_get(self, sender, data):
        self._gpio_output = _KonashiGpioPinsIO.from_buffer_copy(data)
    def _ntf_cb_gpio_input(self, sender, data):
        for i in range(KONASHI_GPIO_COUNT):
            if data[i]&0x10:
                val = data[i]&0x01
                if self._gpio_input[i].level != val:
                    if self._gpio_input_cb is not None:
                        self._gpio_input_cb(i, val)
        self._gpio_input = _KonashiGpioPinsIO.from_buffer_copy(data)
    def _ntf_cb_softpwm_output_get(self, sender, data):
        pass
    def _ntf_cb_hardpwm_output_get(self, sender, data):
        pass
    def _ntf_cb_analog_output_get(self, sender, data):
        pass
    def _ntf_cb_analog_input(self, sender, data):
        pass
    def _ntf_cb_i2c_data_in(self, sender, data):
        pass
    def _ntf_cb_uart_data_in(self, sender, data):
        pass
    def _ntf_cb_uart_data_send_done(self, sender, data):
        pass
    def _ntf_cb_spi_data_in(self, sender, data):
        pass

    def _ntf_cb_builtin_temperature(self, sender, data):
        d = struct.unpack("<h", data)
        temp = d[0]
        temp /= 100
        if self._builtin_temperature_cb is not None:
            self._builtin_temperature_cb(temp)
    def _ntf_cb_builtin_humidity(self, sender, data):
        d = struct.unpack("<h", data)
        hum = d[0]
        hum /= 100
        if self._builtin_humidity_cb is not None:
            self._builtin_humidity_cb(hum)
    def _ntf_cb_builtin_pressure(self, sender, data):
        d = struct.unpack("<i", data)
        press = d[0]
        press /= 1000
        if self._builtin_pressure_cb is not None:
            self._builtin_pressure_cb(press)
    def _ntf_cb_builtin_presence(self, sender, data):
        d = struct.unpack("<?", data)
        pres = d[0]
        if self._builtin_presence_cb is not None:
            self._builtin_presence_cb(pres)
    def _ntf_cb_builtin_accelgyro(self, sender, data):
        d = struct.unpack("<hhhhhh", data)
        accel_x = d[0] / 32768 * 8
        accel_y = d[1] / 32768 * 8
        accel_z = d[2] / 32768 * 8
        gyro_x = d[3] / 32768 * 1000
        gyro_y = d[4] / 32768 * 1000
        gyro_z = d[5] / 32768 * 1000
        if self._builtin_accelgyro_cb is not None:
            self._builtin_accelgyro_cb((accel_x,accel_y,accel_z),(gyro_x,gyro_y,gyro_z))
    def _ntf_cb_builtin_rgb_get(self, sender, data):
        d = struct.unpack("<ccccH", data)
        color = (d[0],d[1],d[2],d[3])
        if self._builtin_rgb_transition_end_cb is not None:
            self._builtin_rgb_transition_end_cb(color)
            self._builtin_rgb_transition_end_cb = None


    async def gpioPinConfigSet(self, configs: Sequence(Tuple[int, bool, KonashiGpioPinConfig])) -> None:
        """
        Specify a list of configurations in the format (pin_bitmask, enable, config) with:
          pin_bitmask (int): a bitmask of the pins to apply this configuration to
          enable (bool): enable or disable the specified pins
          config (KonashiGpioPinConfig): the configuration for the specified pins
        """
        b = bytearray([KONASHI_CFG_CMD_GPIO])
        for config in configs:
            for i in range(KONASHI_GPIO_COUNT):
                if (config[0]&(1<<i)) > 0:
                    if KonashiGpioPinFunction(self._gpio_config[i].function) != KonashiGpioPinFunction.DISABLED and KonashiGpioPinFunction(self._gpio_config[i].function) != KonashiGpioPinFunction.GPIO:
                        raise PinUnavailableError(f'GPIO{i} is already configured as {KONASHI_GPIO_FUNCTION_STR[self._gpio_config[i].function]}')
                    b.extend(bytearray([(i<<4)|(0x1 if config[1] else 0x0), bytes(config[2])[1]]))
        try:
            await self._ble_client.write_gatt_char(KONASHI_UUID_CONFIG_CMD, b)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE write: "{str(e)}"')

    async def gpioPinConfigGet(self, pin_bitmask: int) -> List[KonashiGpioPinConfig]:
        """
        Get a list of current GPIO configurations for the pins specified in the bitmask.
        """
        l = []
        try:
            buf = await self._ble_client.read_gatt_char(KONASHI_UUID_GPIO_CONFIG_GET)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE read: "{str(e)}"')
        self._gpio_config = _KonashiGpioPinsConfig.from_buffer_copy(buf)
        for i in range(KONASHI_GPIO_COUNT):
            if (pin_bitmask&(1<<i)) > 0:
                l.append(self._gpio_config[i])
        return l
    async def gpioPinConfigGetAll(self) -> List[KonashiGpioPinConfig]:
        """
        Get a list of current GPIO configurations for all pins.
        """
        return await self.gpioConfigGet(0xFF)

    def gpioSetInputCallback(self, notify_callback: Callable[[int, int], None]) -> None:
        """
        The callback is called with parameters:
          pin (int)
          value (int)
        """
        self._gpio_input_cb = notify_callback

    async def gpioPinOutputSet(self, controls: Sequence(Tuple[int, KonashiGpioPinControl])) -> None:
        """
        Specify a list of controls in the format (pin, control) with:
          pin (int): a bitmask of the pins to apply this control to
          control (KonashiGpioPinControl): the control for the specified pins
        """
        b = bytearray([KONASHI_CTL_CMD_GPIO])
        for control in controls:
            for i in range(KONASHI_GPIO_COUNT):
                if (control[0]&(1<<i)) > 0:
                    if KonashiGpioPinFunction(self._gpio_config[i].function) != KonashiGpioPinFunction.GPIO:
                        raise PinUnavailableError(f'GPIO{i} is not configured as GPIO (configured as {KONASHI_GPIO_FUNCTION_STR[self._gpio_config[i].function]})')
                    b.extend(bytearray([(i<<4)|(control[1])]))
        try:
            await self._ble_client.write_gatt_char(KONASHI_UUID_CONTROL_CMD, b)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE write: "{str(e)}"')

    async def gpioPinOutputGet(self, pin_bitmask: int) -> List[KonashiGpioPinLevel]:
        """
        Get a list of current GPIO output levels for the pins specified in the bitmask.
        """
        l = []
        try:
            buf = await self._ble_client.read_gatt_char(KONASHI_UUID_GPIO_OUTPUT_GET)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE read: "{str(e)}"')
        self._gpio_output = _KonashiGpioPinsIO.from_buffer_copy(buf)
        for i in range(KONASHI_GPIO_COUNT):
            if (pin_bitmask&(1<<i)) > 0:
                if not self._gpio_output[i].valid:
                    l.append(KonashiGpioPinLevel.INVALID)
                else:
                    l.append(KonashiGpioPinLevel(self._gpio_output[i].level))
        return l
    async def gpioPinOutputGetAll(self) -> List[KonashiGpioPinLevel]:
        """
        Get a list of current GPIO output levels for all pins.
        """
        return await self.gpioOutputGet(0xFF)

    async def gpioPinInputGet(self, pin_bitmask: int) -> List[KonashiGpioPinLevel]:
        """
        Get a list of current GPIO input levels for the pins specified in the bitmask.
        """
        l = []
        try:
            buf = await self._ble_client.read_gatt_char(KONASHI_UUID_GPIO_INPUT)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE read: "{str(e)}"')
        self._gpio_input = _KonashiGpioPinsIO.from_buffer_copy(buf)
        for i in range(KONASHI_GPIO_COUNT):
            if (pin_bitmask&(1<<i)) > 0:
                if not self._gpio_input[i].valid:
                    l.append(KonashiGpioPinLevel.INVALID)
                else:
                    l.append(KonashiGpioPinLevel(self._gpio_input[i].level))
        return l
    async def gpioPinInputGetAll(self) -> List[KonashiGpioPinLevel]:
        """
        Get a list of current GPIO input levels for all pins.
        """
        return await self.gpioInputGet(0xFF)

    async def builtinSetTemperatureCallback(self, notify_callback: Callable[[float], None]) -> None:
        """
        The callback is called with parameters:
          temperature in degrees Celsius (float)
        """
        if notify_callback is not None:
            self._builtin_temperature_cb = notify_callback
            await self._ble_client.start_notify(KONASHI_UUID_BUILTIN_TEMPERATURE, self._ntf_cb_builtin_temperature)
        else:
            await self._ble_client.stop_notify(KONASHI_UUID_BUILTIN_TEMPERATURE)
            self._builtin_temperature_cb = None

    async def builtinSetHumidityCallback(self, notify_callback: Callable[[float], None]) -> None:
        """
        The callback is called with parameters:
          humidity in percent (float)
        """
        if notify_callback is not None:
            self._builtin_humidity_cb = notify_callback
            await self._ble_client.start_notify(KONASHI_UUID_BUILTIN_HUMIDITY, self._ntf_cb_builtin_humidity)
        else:
            await self._ble_client.stop_notify(KONASHI_UUID_BUILTIN_HUMIDITY)
            self._builtin_humidity_cb = None

    async def builtinSetPressureCallback(self, notify_callback: Callable[[float], None]) -> None:
        """
        The callback is called with parameters:
          pressure in hectopascal (float)
        """
        if notify_callback is not None:
            self._builtin_pressure_cb = notify_callback
            await self._ble_client.start_notify(KONASHI_UUID_BUILTIN_PRESSURE, self._ntf_cb_builtin_pressure)
        else:
            await self._ble_client.stop_notify(KONASHI_UUID_BUILTIN_PRESSURE)
            self._builtin_pressure_cb = None

    async def builtinSetPresenceCallback(self, notify_callback: Callable[[bool], None]) -> None:
        """
        The callback is called with parameters:
          presence (bool)
        """
        if notify_callback is not None:
            self._builtin_presence_cb = notify_callback
            await self._ble_client.start_notify(KONASHI_UUID_BUILTIN_PRESENCE, self._ntf_cb_builtin_presence)
        else:
            await self._ble_client.stop_notify(KONASHI_UUID_BUILTIN_PRESENCE)
            self._builtin_presence_cb = None

    async def builtinSetAccelGyroCallback(self, notify_callback: Callable[[(float,float,float),(float,float,float)], None]) -> None:
        """
        The callback is called with parameters:
          accel in g (Tuple(float,float,float))
          gyro in degrees per second (Tuple(float,float,float))
        """
        if notify_callback is not None:
            self._builtin_accelgyro_cb = notify_callback
            await self._ble_client.start_notify(KONASHI_UUID_BUILTIN_ACCELGYRO, self._ntf_cb_builtin_accelgyro)
        else:
            await self._ble_client.stop_notify(KONASHI_UUID_BUILTIN_ACCELGYRO)
            self._builtin_accelgyro_cb = None

    async def builtinSetRgb(self, r: int, g: int, b: int, a: int, duration: int, transition_end_cb: Callable[[(int,int,int,int)], None] = None) -> None:
        """
        Set the RGB LED color.
        r (int): Red (0~255)
        g (int): Green (0~255)
        b (int): Blue (0~255)
        a (int): Alpha (0~255)
        duration (int): duration to new color in milliseconds (0~65535)
        """
        b = bytearray([r&0xFF, g&0xFF, b&0xFF, a&0xFF, (duration&0x00FF), ((duration&0xFF00)>>8)])
        await self._ble_client.write_gatt_char(KONASHI_UUID_BUILTIN_RGB_SET, b)
        if transition_end_cb is not None:
            self._builtin_rgb_transition_end_cb = transition_end_cb

