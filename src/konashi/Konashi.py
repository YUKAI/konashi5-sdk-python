#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import struct
import logging
from ctypes import *
from typing import *
from enum import *

from bleak import *

from .Settings import _Settings
from .Io import _Io
from .Builtin import _Builtin
from .Errors import *


logger = logging.getLogger(__name__)


KONASHI_ADV_SERVICE_UUID = "064d0100-8251-49d9-b6f3-f7ba35e5d0a1"


class Konashi:
    """This class represents a single Konashi device.

    Args:
        name (str): The name (BLE advertising name) of this Konashi device.
    """
    def __init__(self, name: str) -> None:
        """Constructor.
        """
        self._name = name
        self._ble_dev = None
        self._ble_client = None
        self._settings: _Settings = _Settings(self)
        self._io: _Io = _Io(self)
        self._builtin: _Builtin = _Builtin(self)

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


    async def connect(self, timeout: float=0.0) -> None:
        """Connect to this Konashi device.

        If the Konashi class instance was created directly by the user and not returned
        from ``find`` or ``search``, ``find`` will be called internally before the connection
        takes place. In this case, the passed timeout value is also used for ``find``.
        If the Konashi class instance was returned from ``find`` or ``search``, then ``find`` will
        not be called again.

        Args:
            timeout (float, optional): The connection timeout in seconds. Defaults to 0.0.

        Raises:
            KonashiConnectionError: The Konashi device was found but the connection failed.
            NotFoundError: The Konashi device was not found within the timeout time.
            InvalidDeviceError: The specified device name was found but it does not appear to be a valid Konashi device.
        """
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
            logger.debug("Connect to device {}".format(self._name))
            if not timeout > 0.0:
                timeout = None
            _con = await self._ble_client.connect(timeout=timeout)
        except BleakError as e:
            self._ble_client = None
            raise KonashiConnectionError(f'Error occured during BLE connect: "{str(e)}"')
        if _con:
            await self._settings._on_connect()
            await self._io._on_connect()
            await self._builtin._on_connect()

    async def disconnect(self) -> None:
        """Disconnect from this Konashi device.
        """
        if self._ble_client is not None:
            await self._ble_client.disconnect()
            self._ble_client = None

    @property
    def settings(self) -> _Settings:
        """This Konashi devices Settings interface.
        """
        return self._settings

    @property
    def io(self) -> _Io:
        """This Konashi devices I/O interface.
        """
        return self._io

    @property
    def builtin(self) -> _Builtin:
        """This Konashi devices Built-in interface.
        """
        return self._builtin

    @property
    def name(self) -> str:
        """The name (Bluetooth advertising name) of this Konashi device.

        Returns:
            str: The Konashi device name.
        """
        return self._name


class KonashiScanner:
    """This class represents a Konashi scanner.
    """
    def __init__(self) -> None:
        """Constructor.
        """
        self._scanner = None

    @staticmethod
    async def find(name: str, timeout: float=0.0) -> Konashi:
        """Find the Konashi device specified by name. This is a static method.
        If the timeout expires, NotFoundError is raised.
        If the timeout is 0.0, the search continues indefinitely.

        Args:
            name (str): The Konashi device name to search for.
            timeout (float, optional): The search timeout in seconds. Defaults to 0.0.

        Raises:
            NotFoundError: The Konashi device was not found within the timeout time.
            InvalidDeviceError: The specified device name was found but it does not appear to be a valid Konashi device.

        Returns:
            Konashi: The found Konashi device.
        """
        _konashi = None
        _invalid = False
        _scan_task = None
        _scanner = BleakScanner()
        def _scan_cb(dev, adv):
            nonlocal _konashi
            nonlocal _invalid
            if dev.name == name:
                if KONASHI_ADV_SERVICE_UUID in adv.service_uuids:
                    _konashi = Konashi(name)
                    _konashi._ble_dev = dev
                    logger.debug("Found konashi device")
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
                if t > 0:
                    await asyncio.sleep(t)
                else:
                    while True:
                        await asyncio.sleep(100)
                _timedout = True
            except asyncio.CancelledError:
                _timedout = False
            finally:
                await _scanner.stop()
        logger.debug("Scan for device {} (timeout={}s)".format(name, timeout))
        _scan_task = asyncio.create_task(_scan_coro(timeout))
        await _scan_task
        if _timedout:
            raise NotFoundError(f'Could not find {name}')
        elif _invalid:
            raise InvalidDeviceError(f'{name} is not a Konashi device')
        else:
            return _konashi

    @staticmethod
    async def search(timeout: float=10.0) -> List[Konashi]:
        """Search for Konashi devices.
        The search continues for the specified timeout and a list of found devices is returned.

        Args:
            timeout (float, optional): The search timeout in seconds, has to be longer than 0s. Defaults to 10.0.

        Raises:
            ValueError: The timeout value is invalid.

        Returns:
            List[Konashi]: A list of discovered Konashi devices.
        """
        if not timeout > 0.0:
            raise ValueError("Timeout should be longer than 0 seconds")
        _konashi = []
        def _scan_cb(dev, adv):
            nonlocal _konashi
            if KONASHI_ADV_SERVICE_UUID in adv.service_uuids:
                k = Konashi(dev.name)
                k._ble_dev = dev
                if k not in _konashi:
                    logger.debug("Discovered new konashi: {}".format(dev.name))
                    _konashi.append(k)
        _scanner = BleakScanner()
        _scanner.register_detection_callback(_scan_cb)
        logger.debug("Start searching for konashi")
        await _scanner.start()
        await asyncio.sleep(timeout)
        _scanner.register_detection_callback(None)
        await _scanner.stop()
        logger.debug("Finished searching for konashi")
        return _konashi

    async def scan_start(self, cb: Callable[[Konashi], None]) -> None:
        """Start scanning for Konashi devices.
        The search continues until cancelled and the callback is called when a device is discovered.

        Args:
            cb (Callable[[Konashi], None]): The callback for discovered devices.

        Returns:
            List[Konashi]: A list of discovered Konashi devices.
        """
        if self._scanner is not None:
            return
        def _scan_cb(dev, adv):
            if KONASHI_ADV_SERVICE_UUID in adv.service_uuids:
                k = Konashi(dev.name)
                k._ble_dev = dev
                cb(k)
        self._scanner = BleakScanner()
        self._scanner.register_detection_callback(_scan_cb)
        await self._scanner.start()
        logger.debug("Started scanning for konashi")

    async def scan_stop(self) -> None:
        if self._scanner is None:
            return
        self._scanner.register_detection_callback(None)
        await self._scanner.stop()
        self._scanner = None
        logger.debug("Finished scanning for konashi")

    @property
    def is_scanning(self) -> bool:
        """Indicates if this scanner instance is currently scanning.

        Returns:
            bool: True is the scanner is scanning, otherwise False.
        """
        return self._scanner is not None
