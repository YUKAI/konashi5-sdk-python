#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import struct
from ctypes import *
from typing import *
from enum import *

from bleak import *

from .settings import Settings


KONASHI_ADV_SERVICE_UUID = "064d0100-8251-49d9-b6f3-f7ba35e5d0a1"

KONASHI_UUID_SETTINGS_CMD = "064d0101-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_SET_CMD_SYSTEM = 0x01
KONASHI_SET_CMD_BLUETOOTH = 0x02
KONASHI_UUID_SYSTEM_SETTINGS_GET = "064d0102-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_UUID_BLUETOOTH_SETTINGS_GET = "064d0103-8251-49d9-b6f3-f7ba35e5d0a1"

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


### Bluetooth
class KonashiBluetoothFunction(IntEnum):
    MESH = 0
    EX_ADVERTISE = 1
class KonashiBluetoothPrimaryPhy(IntEnum):
    ONE_M_PHY = 0x01
    CODED_PHY = 0x04
class KonashiBluetoothSecondaryPhy(IntEnum):
    ONE_M_PHY = 0x01
    TWO_M_PHY = 0x02
    CODED_PHY = 0x04
class KonashiBluetoothConnectionPhy(IntFlag):
    ONE_M_PHY_UNCODED  = 0x01
    TWO_M_PHY_UNCODED  = 0x02
    CODED_PHY_125k     = 0x04
    CODED_PHY_500k     = 0x08
class KonashiBluetoothExAdvertiseContents(IntFlag):
    NONE         = 0x00000000
    DEVICE_NAME  = 0x01000000
    UUID128      = 0x02000000
    MANUF_DATA   = 0x04000000
    BLE_ALL      = 0x07000000
    GPIO7_IN     = 0x00800000
    GPIO6_IN     = 0x00400000
    GPIO5_IN     = 0x00200000
    GPIO4_IN     = 0x00100000
    GPIO3_IN     = 0x00080000
    GPIO2_IN     = 0x00040000
    GPIO1_IN     = 0x00020000
    GPIO0_IN     = 0x00010000
    GPIO_IN_ALL  = 0x00FF0000
    AIO2_IN      = 0x00004000
    AIO1_IN      = 0x00002000
    AIO0_IN      = 0x00001000
    AIO_IN_ALL   = 0x00007000
class KonashiBluetoothSettings(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('enabled_functions', c_uint8),
        ('main_conn_pref_phy', c_uint8, 4),
        ('main_adv_sec_phy', c_uint8, 4),
        ('ex_adv_sec_phy', c_uint8, 4),
        ('ex_adv_prim_phy', c_uint8, 4),
        ('ex_adv_contents', c_uint32, 28),
        ('ex_adv_status', c_uint32, 4)
    ]
    def __str__(self):
        s = "KonashiBluetoothSettings("
        s += "EN=0x{:02x}".format(self.enabled_functions)
        s += ", MainAdvSecPHY=0x{:01x}".format(self.main_adv_sec_phy)
        s += ", MainConnPHY=0x{:01x}".format(self.main_conn_pref_phy)
        s += ", ExAdvPrimPHY=0x{:01x}".format(self.ex_adv_prim_phy)
        s += ", ExAdvSecPHY=0x{:01x}".format(self.ex_adv_sec_phy)
        s += ", ExAdvStatus=0x{:01x}".format(self.ex_adv_status)
        s += ", ExAdvContents=0x{:07x}".format(self.ex_adv_contents)
        s += ")"
        return s


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
            if self.function == KonashiGpioPinFunction.GPIO:
                s += ", "
                s += "OD" if self.wired_fct==KonashiGpioPinWiredFunction.OPEN_DRAIN else "OS" if self.wired_fct==KonashiGpioPinWiredFunction.OPEN_SOURCE else "OUT" if self.direction==KonashiGpioPinDirection.OUTPUT else "IN"
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


### SoftPWM
KONASHI_SOFTPWM_COUNT = 4
KONASHI_SOFTPWM_PIN_TO_GPIO_NUM = [4, 5, 6, 7]
class KonashiSoftpwmControlType(Enum):
    DISABLED = 0
    DUTY = 1
    PERIOD = 2
    def __int__(self):
        return self.value
class KonashiSoftpwmPinConfig(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('control_type', c_uint8, 4),
        ('', c_uint8, 4),
        ('fixed_value', c_uint16)
    ]
    def __init__(self, control_type: KonashiSoftpwmControlType, fixed_value: int=0):
        """
        control_type (KonashiSoftpwmControlType): the control type for the pin
        fixed_value (int): the fixed value:
            if control_type is DUTY, this is the fixed period in units of 100us (valid range: [0,65535])
            if control_type is PERIOD, this is the fixed duty cycle in units of 0.1% (valid range: [0,1000])
        """
        self.control_type = int(control_type)
        if control_type == KonashiSoftpwmControlType.DUTY:
            if fixed_value < 0 or fixed_value > 65535:
                raise ValueError("The valid range for the fixed period is [0,65535] (unit: 100us)")
        elif control_type == KonashiSoftpwmControlType.PERIOD:
            if fixed_value < 0 or fixed_value > 1000:
                raise ValueError("The valid range for the fixed duty cycle is [0,1000] (unit: 0.1%)")
        self.fixed_value = fixed_value
    def __str__(self):
        s = "KonashiSoftpwmPinConfig("
        s += "DUTY control" if self.control_type==KonashiSoftpwmControlType.DUTY else "PERIOD control" if self.control_type==KonashiSoftpwmControlType.PERIOD else "DISABLED"
        if self.control_type != KonashiSoftpwmControlType.DISABLED:
            s += ", "
            s += str(self.fixed_value*0.1)
            if self.control_type == KonashiSoftpwmControlType.DUTY:
                s += "ms fixed period"
            else:
                s += r"% fixed duty cycle"
        s += ")"
        return s
_KonashiSoftpwmPinsConfig = KonashiSoftpwmPinConfig*KONASHI_SOFTPWM_COUNT

class KonashiSoftpwmPinControl(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('control_value', c_uint16),
        ('transition_duration', c_uint16)
    ]
    def __init__(self, control_value: int, transition_duration: int=0):
        """
        control_value (int): the control value to apply to the pin:
            if control_type is DUTY, this is the duty cycle control value in units of 0.1% (valid range: [0,1000])
            if control_type is PERIOD, this is the period control value in units of 100us (valid range: [0,65535])
        transition_duration (int): duration to reach the target value in untis of 1ms (valid range: [0,65535])
        """
        if control_value < 0 or control_value > 65535:
            raise ValueError("The valid range for the control value is at least [0,65535]")
        if transition_duration < 0 or control_value > 65535:
            raise ValueError("The valid range for the transition duration is [0,65535] (unit: 1ms)")
        self.control_value = control_value
        self.transition_duration = transition_duration
        self.control_type = None
    def __str__(self):
        s = "KonashiSoftpwmPinControl("
        if self.control_type is None:
            s += "Control value "+str(self.control_value)+" raw, Transition duration "+str(self.transition_duration)+"ms"
        else:
            if self.control_type == KonashiSoftpwmControlType.DISABLED:
                s += "DISABLED"
            else:
                s += int(self.control_value*0.1)
                if self.control_type == KonashiSoftpwmControlType.PERIOD:
                    s += "ms period"
                else:
                    s += r"% duty cycle"
                s += ", Transition duration "+str(self.transition_duration)+"ms"
        s += ")"
        return s
_KonashiSoftpwmPinsControl = KonashiSoftpwmPinControl*KONASHI_SOFTPWM_COUNT


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
        self._settings: Settings = Settings(self)
        self._bluetooth_settings: KonashiBluetoothSettings = KonashiBluetoothSettings()
        self._gpio_config = _KonashiGpioPinsConfig()
        self._gpio_output = _KonashiGpioPinsIO()
        self._gpio_input = _KonashiGpioPinsIO()
        self._gpio_input_cb = None
        self._softpwm_config = _KonashiSoftpwmPinsConfig()
        self._softpwm_output = _KonashiSoftpwmPinsControl()
        self._softpwm_trans_end_cb = None
        self._softpwm_ongoing_control = []
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
            await self.settings.system._on_connect()
            buf = await self._ble_client.read_gatt_char(KONASHI_UUID_BLUETOOTH_SETTINGS_GET)
            buf[3:7] = buf[-1:]+buf[-2:-1]+buf[-3:-2]+buf[-4:-3]
            self._bluetooth_settings = KonashiBluetoothSettings.from_buffer_copy(buf)
            await self._ble_client.start_notify(KONASHI_UUID_BLUETOOTH_SETTINGS_GET, self._ntf_cb_bluetooth_settings)

            buf = await self._ble_client.read_gatt_char(KONASHI_UUID_GPIO_CONFIG_GET)
            self._gpio_config = _KonashiGpioPinsConfig.from_buffer_copy(buf)
            await self._ble_client.start_notify(KONASHI_UUID_GPIO_CONFIG_GET, self._ntf_cb_gpio_config_get)
            buf = await self._ble_client.read_gatt_char(KONASHI_UUID_SOFTPWM_CONFIG_GET)
            self._softpwm_config = _KonashiSoftpwmPinsConfig.from_buffer_copy(buf)
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
            buf = await self._ble_client.read_gatt_char(KONASHI_UUID_SOFTPWM_OUTPUT_GET)
            self._softpwm_output = _KonashiSoftpwmPinsControl.from_buffer_copy(buf)
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

    @property
    def settings(self) -> Settings:
        return self._settings

    def _ntf_cb_bluetooth_settings(self, sender, data):
        data[3:7] = data[-1:]+data[-2:-1]+data[-3:-2]+data[-4:-3]
        self._bluetooth_settings = KonashiBluetoothSettings.from_buffer_copy(data)

    def _ntf_cb_gpio_config_get(self, sender, data):
        self._gpio_config = _KonashiGpioPinsConfig.from_buffer_copy(data)
    def _ntf_cb_softpwm_config_get(self, sender, data):
        self._softpwm_config = _KonashiSoftpwmPinsConfig.from_buffer_copy(data)
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
        self._softpwm_output = _KonashiSoftpwmPinsControl.from_buffer_copy(data)
        for i in range(KONASHI_SOFTPWM_COUNT):
            if i in self._softpwm_ongoing_control and self._softpwm_output[i].transition_duration == 0:
                self._softpwm_ongoing_control.remove(i)
                self._softpwm_trans_end_cb(i)
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


    ### Bluetooth
    async def bluetoothSettingsGet(self) -> KonashiBluetoothSettings:
        try:
            buf = await self._ble_client.read_gatt_char(KONASHI_UUID_BLUETOOTH_SETTINGS_GET)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE read: "{str(e)}"')
        buf[3:7] = buf[-1:]+buf[-2:-1]+buf[-3:-2]+buf[-4:-3]
        self._bluetooth_settings = KonashiBluetoothSettings.from_buffer_copy(buf)
        return self._bluetooth_settings

    async def bluetoothSettingsFunctionEnable(self, function: KonashiBluetoothFunction, enable: bool) -> None:
        b = bytearray([KONASHI_SET_CMD_BLUETOOTH, (function<<4)+enable])
        try:
            await self._ble_client.write_gatt_char(KONASHI_UUID_SETTINGS_CMD, b)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE write: "{str(e)}"')

    async def bluetoothSettingSetsMainAdvSecPhy(self, phy: KonashiBluetoothSecondaryPhy) -> None:
        b = bytearray([KONASHI_SET_CMD_BLUETOOTH, 0xF0+phy])
        try:
            await self._ble_client.write_gatt_char(KONASHI_UUID_SETTINGS_CMD, b)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE write: "{str(e)}"')

    async def bluetoothSettingsSetMainPreferredConnPhy(self, phy: KonashiBluetoothConnectionPhy) -> None:
        b = bytearray([KONASHI_SET_CMD_BLUETOOTH, 0xE0+phy])
        try:
            await self._ble_client.write_gatt_char(KONASHI_UUID_SETTINGS_CMD, b)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE write: "{str(e)}"')

    async def bluetoothSettingsSetExAdvPhy(self, prim_phy: KonashiBluetoothPrimaryPhy, sec_phy: KonashiBluetoothSecondaryPhy) -> None:
        b = bytearray([KONASHI_SET_CMD_BLUETOOTH, 0xD0+prim_phy, 0xC0+sec_phy])
        try:
            await self._ble_client.write_gatt_char(KONASHI_UUID_SETTINGS_CMD, b)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE write: "{str(e)}"')

    async def bluetoothSettingsSetExAdvContents(self, contents: KonashiBluetoothExAdvertiseContents) -> None:
        b = bytearray([KONASHI_SET_CMD_BLUETOOTH, 0xB0+((contents>>24)&0x0F), (contents>>16)&0xFF, (contents>>8)&0xFF, (contents>>0)&0xFF])
        try:
            await self._ble_client.write_gatt_char(KONASHI_UUID_SETTINGS_CMD, b)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE write: "{str(e)}"')


    ### GPIO
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
                        raise PinUnavailableError(f'Pin {i} is already configured as {KONASHI_GPIO_FUNCTION_STR[self._gpio_config[i].function]}')
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
        return await self.gpioPinConfigGet(0xFF)

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
                        raise PinUnavailableError(f'Pin {i} is not configured as GPIO (configured as {KONASHI_GPIO_FUNCTION_STR[self._gpio_config[i].function]})')
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
        return await self.gpioPinOutputGet(0xFF)

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


    ### SoftPWM
    async def softpwmPinConfigSet(self, configs: Sequence(Tuple[int, KonashiSoftpwmPinConfig])) -> None:
        """
        Specify a list of configurations in the format (pin_bitmask, config) with:
          pin_bitmask (int): a bitmask of the pins to apply this configuration to
          config (KonashiSoftpwmPinConfig): the configuration for the specified pins
        """
        b = bytearray([KONASHI_CFG_CMD_SOFTPWM])
        for config in configs:
            for i in range(KONASHI_SOFTPWM_COUNT):
                if (config[0]&(1<<i)) > 0:
                    if self._gpio_config[KONASHI_SOFTPWM_PIN_TO_GPIO_NUM[i]].function != int(KonashiGpioPinFunction.DISABLED) and self._gpio_config[KONASHI_SOFTPWM_PIN_TO_GPIO_NUM[i]].function != int(KonashiGpioPinFunction.PWM):
                        raise PinUnavailableError(f'Pin {KONASHI_SOFTPWM_PIN_TO_GPIO_NUM[i]} is already configured as {KONASHI_GPIO_FUNCTION_STR[self._gpio_config[KONASHI_SOFTPWM_PIN_TO_GPIO_NUM[i]].function]}')
                    b.extend(bytearray([(i<<4)|(bytes(config[1])[0])]) + bytearray(config[1])[1:3])
        try:
            await self._ble_client.write_gatt_char(KONASHI_UUID_CONFIG_CMD, b)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE write: "{str(e)}"')

    async def softpwmPinConfigGet(self, pin_bitmask: int) -> List[KonashiSoftpwmPinConfig]:
        """
        Get a list of current SoftPWM configurations for the pins specified in the bitmask.
        """
        l = []
        try:
            buf = await self._ble_client.read_gatt_char(KONASHI_UUID_SOFTPWM_CONFIG_GET)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE read: "{str(e)}"')
        self._softpwm_config = _KonashiSoftpwmPinsConfig.from_buffer_copy(buf)
        for i in range(KONASHI_SOFTPWM_COUNT):
            if (pin_bitmask&(1<<i)) > 0:
                l.append(self._softpwm_config[i])
        return l
    async def softpwmPinConfigGetAll(self) -> List[KonashiSoftpwmPinConfig]:
        """
        Get a list of current SoftPWM configurations for all pins.
        """
        return await self.softpwmPinConfigGet(0x0F)

    def softpwmSetTransitionEndCallback(self, notify_callback: Callable[[int], None]) -> None:
        """
        The callback is called with parameters:
          pin (int)
        """
        self._softpwm_trans_end_cb = notify_callback

    async def softpwmPinOutputSet(self, controls: Sequence(Tuple[int, KonashiSoftpwmPinControl])) -> None:
        """
        Specify a list of controls in the format (pin, control) with:
          pin (int): a bitmask of the pins to apply this control to
          control (KonashiSoftpwmPinControl): the control for the specified pins
        """
        ongoing_control = []
        b = bytearray([KONASHI_CTL_CMD_SOFTPWM])
        for control in controls:
            for i in range(KONASHI_SOFTPWM_COUNT):
                if (control[0]&(1<<i)) > 0:
                    if self._gpio_config[KONASHI_SOFTPWM_PIN_TO_GPIO_NUM[i]].function != int(KonashiGpioPinFunction.PWM):
                        raise PinUnavailableError(f'Pin {KONASHI_SOFTPWM_PIN_TO_GPIO_NUM[i]} is not configured as PWM (configured as {KONASHI_GPIO_FUNCTION_STR[self._gpio_config[KONASHI_SOFTPWM_PIN_TO_GPIO_NUM[i]].function]})')
                    if self._softpwm_config[i].control_type == int(KonashiSoftpwmControlType.DUTY):
                        if control[1].control_value < 0 or control[1].control_value > 1000:
                            raise ValueError("The valid range for the duty cycle control is [0,1000] (unit: 0.1%)")
                    elif self._softpwm_config[i].control_type == int(KonashiSoftpwmControlType.PERIOD):
                        if control[1].control_value < 0 or control[1].control_value > 65535:
                            raise ValueError("The valid range for the period control is [0,65535] (unit: 100us)")
                    else:
                        raise PinUnavailableError(f'SoftPWM{i} is not enabled')
                    b.extend(bytearray([i])+bytearray(control[1]))
                    ongoing_control.append(i)
        try:
            for i in ongoing_control:
                if i not in self._softpwm_ongoing_control:
                    self._softpwm_ongoing_control.append(i)
            await self._ble_client.write_gatt_char(KONASHI_UUID_CONTROL_CMD, b)
        except BleakError as e:
            for i in ongoing_control:
                if i in self._softpwm_ongoing_control:
                    self._softpwm_ongoing_control.remove(i)
            raise KonashiError(f'Error occured during BLE write: "{str(e)}"')

    async def softpwmPinOutputGet(self, pin_bitmask: int) -> List[KonashiSoftpwmPinControl]:
        """
        Get a list of current SoftPWM output control for the pins specified in the bitmask.
        """
        l = []
        try:
            buf = await self._ble_client.read_gatt_char(KONASHI_UUID_SOFTPWM_OUTPUT_GET)
        except BleakError as e:
            raise KonashiError(f'Error occured during BLE read: "{str(e)}"')
        self._softpwm_output = _KonashiSoftpwmPinsControl.from_buffer_copy(buf)
        for i in range(KONASHI_SOFTPWM_COUNT):
            if (pin_bitmask&(1<<i)) > 0:
                ctrl = self._softpwm_output[i]
                ctrl.control_type = self._softpwm_config[i].control_type
                l.append(ctrl)
        return l
    async def softpwmPinOutputGetAll(self) -> List[KonashiSoftpwmPinControl]:
        """
        Get a list of current SoftPWM output control for all pins.
        """
        return await self.softpwmPinOutputGet(0x0F)




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

