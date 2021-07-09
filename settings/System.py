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

KONASHI_UUID_SETTINGS_CMD = "064d0101-8251-49d9-b6f3-f7ba35e5d0a1"
KONASHI_SET_CMD_SYSTEM = 0x01
KONASHI_UUID_SYSTEM_SETTINGS_GET = "064d0102-8251-49d9-b6f3-f7ba35e5d0a1"


class _Command(IntEnum):
    NVM_USE_SET = 1
    NVM_SAVE_TRIGGER_SET = 2
    NVM_SAVE_NOW = 3
    NVM_ERASE_NOW = 4
    FCT_BTN_EMULATE_PRESS = 5
    FCT_BTN_EMULATE_LONG_PRESS = 6
    FCT_BTN_EMULATE_VERY_LONG_PRESS = 7
class NvmUse(IntEnum):
    DISABLED = 0
    ENABLED = 1
class NvmSaveTrigger(IntEnum):
    AUTO = 0
    MANUAL = 1
class Settings(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('nvm_use', c_uint8),
        ('nvm_save_trigger', c_uint8)
    ]
    def __str__(self):
        s = "KonashiSettingsSystemSettings("
        if self.nvm_use == NvmUse.ENABLED:
            s += "NVM enabled"
            s += ", NVM save " + ("auto" if self.nvm_save_trigger==NvmSaveTrigger.AUTO else "manual")
        else:
            s += "NVM disabled"
        s += ")"
        return s


class System(KonashiElementBase._KonashiElementBase):
    def __init__(self, konashi) -> None:
        super().__init__(konashi)
        self._settings: Settings = Settings()

    def __str__(self):
        s = "KonashiSettingsSystem("
        if self.nvm_use == NvmUse.ENABLED:
            s += "NVM enabled"
            s += ", NVM save " + ("auto" if self.nvm_save_trigger==NvmSaveTrigger.AUTO else "manual")
        else:
            s += "NVM disabled"
        s += ")"
        return s

    def __repr__(self):
        return f'Konashi(name="{self._name}")'

    def __eq__(self, other):
        if self._ble_dev is not None and other._ble_dev is not None:
            return self._ble_dev.address == other._ble_dev.address
        return self._name == other._name

    def __ne__(self, other):
        return not self.__eq__(other)


    async def _on_connect(self) -> None:
        await self._enable_notify(KONASHI_UUID_SYSTEM_SETTINGS_GET, self._ntf_cb_settings)
        await self._read(KONASHI_UUID_SYSTEM_SETTINGS_GET)


    def _ntf_cb_settings(self, sender, data):
        self._settings = Settings.from_buffer_copy(data)


    async def get_settings(self) -> Settings:
        await self._read(KONASHI_UUID_SYSTEM_SETTINGS_GET)
        return self._settings

    async def get_nvm_use(self) -> bool:
        await self._read(KONASHI_UUID_SYSTEM_SETTINGS_GET)
        return True if self._settings.nvm_use==NvmUse.ENABLED else False

    async def set_nvm_use(self, enable: bool) -> None:
        b = bytearray([KONASHI_SET_CMD_SYSTEM, _Command.NVM_USE_SET, enable])
        await self._write(KONASHI_UUID_SETTINGS_CMD, b)

    async def get_nvm_save_trigger(self) -> NvmSaveTrigger:
        await self._read(KONASHI_UUID_SYSTEM_SETTINGS_GET)
        return self._settings.nvm_save_trigger

    async def set_nvm_save_trigger(self, trigger: NvmSaveTrigger) -> None:
        b = bytearray([KONASHI_SET_CMD_SYSTEM, _Command.NVM_SAVE_TRIGGER_SET, trigger])
        await self._write(KONASHI_UUID_SETTINGS_CMD, b)

    async def nvm_save_now(self) -> None:
        b = bytearray([KONASHI_SET_CMD_SYSTEM, _Command.NVM_SAVE_NOW])
        await self._write(KONASHI_UUID_SETTINGS_CMD, b)

    async def nvm_erase_now(self) -> None:
        b = bytearray([KONASHI_SET_CMD_SYSTEM, _Command.NVM_ERASE_NOW])
        await self._write(KONASHI_UUID_SETTINGS_CMD, b)

    async def emul_press(self) -> None:
        b = bytearray([KONASHI_SET_CMD_SYSTEM, _Command.FCT_BTN_EMULATE_PRESS])
        await self._write(KONASHI_UUID_SETTINGS_CMD, b)

    async def emul_long_press(self) -> None:
        b = bytearray([KONASHI_SET_CMD_SYSTEM, _Command.FCT_BTN_EMULATE_LONG_PRESS])
        await self._write(KONASHI_UUID_SETTINGS_CMD, b)

    async def emul_very_long_press(self) -> None:
        b = bytearray([KONASHI_SET_CMD_SYSTEM, _Command.FCT_BTN_EMULATE_VERY_LONG_PRESS])
        await self._write(KONASHI_UUID_SETTINGS_CMD, b)
