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


KONASHI_UUID_SETTINGS_CMD = "064d0101-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_SET_CMD_BLUETOOTH = 0x02
KONASHI_UUID_BLUETOOTH_SETTINGS_GET = "064d0103-8251-49d9-b6f3-f7ba35e5d0a1"


class BluetoothSettingsFunction(IntEnum):
    MESH = 0
    EX_ADVERTISER = 1
class BluetoothSettingsPrimaryPhy(IntEnum):
    ONE_M_PHY = 0x01
    CODED_PHY = 0x04
class BluetoothSettingsSecondaryPhy(IntEnum):
    ONE_M_PHY = 0x01
    TWO_M_PHY = 0x02
    CODED_PHY = 0x04
class BluetoothSettingsConnectionPhy(IntFlag):
    ONE_M_PHY_UNCODED  = 0x01
    TWO_M_PHY_UNCODED  = 0x02
    CODED_PHY_125k     = 0x04
    CODED_PHY_500k     = 0x08
class BluetoothSettingsExAdvertiseContents(IntFlag):
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
class BluetoothSettingsExAdvertiseStatus(IntEnum):
    DISABLED  = 0x0
    LEGACY    = 0x1
    EXTENDED  = 0x2
    ERROR     = 0xF
class _BluetoothSettings(LittleEndianStructure):
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
        s = "KonashiSettingsBluetoothSettings("
        s += "EN=0x{:02x}".format(self.enabled_functions)
        s += ", MainAdvSecPHY=0x{:01x}".format(self.main_adv_sec_phy)
        s += ", MainConnPHY=0x{:01x}".format(self.main_conn_pref_phy)
        s += ", ExAdvPrimPHY=0x{:01x}".format(self.ex_adv_prim_phy)
        s += ", ExAdvSecPHY=0x{:01x}".format(self.ex_adv_sec_phy)
        s += ", ExAdvStatus=0x{:01x}".format(self.ex_adv_status)
        s += ", ExAdvContents=0x{:07x}".format(self.ex_adv_contents)
        s += ")"
        return s


class _Bluetooth(KonashiElementBase._KonashiElementBase):
    def __init__(self, konashi) -> None:
        super().__init__(konashi)
        self._settings: _BluetoothSettings = _BluetoothSettings()

    def __str__(self):
        s = "KonashiSettingsBluetooth("
        s += "EN=0x{:02x}".format(self.enabled_functions)
        s += ", MainAdvSecPHY=0x{:01x}".format(self.main_adv_sec_phy)
        s += ", MainConnPHY=0x{:01x}".format(self.main_conn_pref_phy)
        s += ", ExAdvPrimPHY=0x{:01x}".format(self.ex_adv_prim_phy)
        s += ", ExAdvSecPHY=0x{:01x}".format(self.ex_adv_sec_phy)
        s += ", ExAdvStatus=0x{:01x}".format(self.ex_adv_status)
        s += ", ExAdvContents=0x{:07x}".format(self.ex_adv_contents)
        s += ")"
        return s

    def __repr__(self):
        s = "KonashiSettingsBluetooth("
        s += "EN=0x{:02x}".format(self.enabled_functions)
        s += ", MainAdvSecPHY=0x{:01x}".format(self.main_adv_sec_phy)
        s += ", MainConnPHY=0x{:01x}".format(self.main_conn_pref_phy)
        s += ", ExAdvPrimPHY=0x{:01x}".format(self.ex_adv_prim_phy)
        s += ", ExAdvSecPHY=0x{:01x}".format(self.ex_adv_sec_phy)
        s += ", ExAdvStatus=0x{:01x}".format(self.ex_adv_status)
        s += ", ExAdvContents=0x{:07x}".format(self.ex_adv_contents)
        s += ")"
        return s


    async def _on_connect(self) -> None:
        await self._enable_notify(KONASHI_UUID_BLUETOOTH_SETTINGS_GET, self._ntf_cb_settings)
        await self._read(KONASHI_UUID_BLUETOOTH_SETTINGS_GET)
        

    def _ntf_cb_settings(self, sender, data):
        logger.debug("Received settings data: {}".format("".join("{:02x}".format(x) for x in data)))
        data[3:7] = data[-1:]+data[-2:-1]+data[-3:-2]+data[-4:-3]
        self._settings = _BluetoothSettings.from_buffer_copy(data)


    async def get_settings(self) -> _BluetoothSettings:
        """Get the current Bluetooth settings.

        Returns:
            _BluetoothSettings: The current bluetooth settings.
                This class has 7 members:
                    enabled_functions: A bitmask of enabled Bluetooth functions, see ``BluetoothSettingsFunction``.
                    main_conn_pref_phy: The main connection preferred PHY, see ``BluetoothSettingsConnectionPhy``.
                    main_adv_sec_phy: The main advertising secondary PHY, see ``BluetoothSettingsSecondaryPhy``.
                    ex_adv_sec_phy: The secondary advertiser secondary PHY, see ``BluetoothSettingsSecondaryPhy``.
                    ex_adv_prim_phy: The secondary advertiser primary PHY, see ``BluetoothSettingsPrimaryPhy``.
                    ex_adv_contents: A bitmask of the secondary advertiser contents, see ``BluetoothSettingsExAdvertiseContents``.
                    ex_adv_status: The secondary advertiser status, see ``BluetoothSettingsExAdvertiseStatus``.
        """
        await self._read(KONASHI_UUID_BLUETOOTH_SETTINGS_GET)
        return self._settings

    async def enable_function(self, function: BluetoothSettingsFunction, enable: bool) -> None:
        """Enable or disable a Bluetooth functionality.

        Args:
            function (BluetoothSettingsFunction): The function to enable or disable.
            enable (bool): True to enable, False to disable.
        """
        b = bytearray([KONASHI_SET_CMD_BLUETOOTH, (function<<4)+enable])
        await self._write(KONASHI_UUID_SETTINGS_CMD, b)

    async def set_main_adv_sec_phy(self, phy: BluetoothSettingsSecondaryPhy) -> None:
        """Set the main advertiser Secondary PHY.

        Args:
            phy (BluetoothSettingsSecondaryPhy): The secondary PHY type.
        """
        b = bytearray([KONASHI_SET_CMD_BLUETOOTH, 0xF0+phy])
        await self._write(KONASHI_UUID_SETTINGS_CMD, b)

    async def set_main_preferred_conn_phy(self, phy: BluetoothSettingsConnectionPhy) -> None:
        """Set the main preferred connection PHYs.
        Multiple preferred PHYs can be set in the form of a bitmask.

        Args:
            phy (BluetoothSettingsConnectionPhy): The preferred connection PHYs
        """
        b = bytearray([KONASHI_SET_CMD_BLUETOOTH, 0xE0+phy])
        await self._write(KONASHI_UUID_SETTINGS_CMD, b)

    async def set_ex_adv_phy(self, prim_phy: BluetoothSettingsPrimaryPhy, sec_phy: BluetoothSettingsSecondaryPhy) -> None:
        """Set the secondary advertiser primary and secondary PHYs.

        Args:
            prim_phy (BluetoothSettingsPrimaryPhy): The primary PHY.
            sec_phy (BluetoothSettingsSecondaryPhy): The secondary PHY.
        """
        b = bytearray([KONASHI_SET_CMD_BLUETOOTH, 0xD0+prim_phy, 0xC0+sec_phy])
        await self._write(KONASHI_UUID_SETTINGS_CMD, b)

    async def set_ex_adv_contents(self, contents: BluetoothSettingsExAdvertiseContents) -> None:
        """Set the secondary advertiser advertising contents.
        If the resulting advertising data length is longer than 31 bytes,
        advertising will automatically be in extended mode, otherwise it will be legacy mode.

        Args:
            contents (BluetoothSettingsExAdvertiseContents): A mask of the contents to show.
        """
        b = bytearray([KONASHI_SET_CMD_BLUETOOTH, 0xB0+((contents>>24)&0x0F), (contents>>16)&0xFF, (contents>>8)&0xFF, (contents>>0)&0xFF])
        await self._write(KONASHI_UUID_SETTINGS_CMD, b)
