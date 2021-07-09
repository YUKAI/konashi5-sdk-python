#!/usr/bin/env python3

from .System import System


class Settings:
    def __init__(self, konashi):
        self._system = System(konashi)

    @property
    def system(self) -> System:
        return self._system
