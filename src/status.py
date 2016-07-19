#! /usr/bin/python3

from enum import IntEnum

class Status(IntEnum):
    UNLOCKED = 0
    LOCKED_IDLE = 1
    LOCKED_AWAKE = 2
    AUTHENTICATING = 3

ScreensaverStatus = Status.UNLOCKED
