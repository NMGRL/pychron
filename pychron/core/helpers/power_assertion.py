"""macOS IOPMAssertion wrapper.

Pychron experiments run for hours. If the Mac goes to idle/display sleep
mid-run the Qt CFRunLoop is suspended, timers stall, and the app appears
hung on wake. Holding an IOPMAssertion of type
PreventUserIdleSystemSleep keeps the system awake while an experiment is
active.

Pure ctypes, no pyobjc dependency. No-op on non-Darwin.
"""
from __future__ import annotations

import ctypes
import logging
import sys
from ctypes import byref, c_char_p, c_int, c_uint32, c_void_p

_log = logging.getLogger("pychron.power_assertion")

_kCFStringEncodingUTF8 = 0x08000100
_kIOPMAssertionLevelOn = 255
_kIOPMAssertionLevelOff = 0

_ASSERTION_TYPE = b"PreventUserIdleSystemSleep"

_assertion_id: c_uint32 | None = None
_IOKit = None
_CF = None


def _load() -> bool:
    global _IOKit, _CF
    if sys.platform != "darwin":
        return False
    if _IOKit is not None:
        return True
    try:
        _CF = ctypes.CDLL(
            "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
        )
        _IOKit = ctypes.CDLL("/System/Library/Frameworks/IOKit.framework/IOKit")
    except OSError as e:
        _log.warning("power_assertion: failed to load frameworks: %s", e)
        return False

    _CF.CFStringCreateWithCString.restype = c_void_p
    _CF.CFStringCreateWithCString.argtypes = [c_void_p, c_char_p, c_uint32]
    _CF.CFRelease.restype = None
    _CF.CFRelease.argtypes = [c_void_p]

    _IOKit.IOPMAssertionCreateWithName.restype = c_int
    _IOKit.IOPMAssertionCreateWithName.argtypes = [
        c_void_p,
        c_uint32,
        c_void_p,
        ctypes.POINTER(c_uint32),
    ]
    _IOKit.IOPMAssertionRelease.restype = c_int
    _IOKit.IOPMAssertionRelease.argtypes = [c_uint32]
    return True


def acquire(name: str = "pychron experiment running") -> bool:
    """Acquire PreventUserIdleSystemSleep assertion. Idempotent."""
    global _assertion_id
    if _assertion_id is not None:
        return True
    if not _load():
        return False

    cf_type = _CF.CFStringCreateWithCString(None, _ASSERTION_TYPE, _kCFStringEncodingUTF8)
    cf_name = _CF.CFStringCreateWithCString(
        None, name.encode("utf-8"), _kCFStringEncodingUTF8
    )
    if not cf_type or not cf_name:
        _log.warning("power_assertion: CFStringCreateWithCString failed")
        if cf_type:
            _CF.CFRelease(cf_type)
        if cf_name:
            _CF.CFRelease(cf_name)
        return False

    aid = c_uint32(0)
    rc = _IOKit.IOPMAssertionCreateWithName(
        cf_type, _kIOPMAssertionLevelOn, cf_name, byref(aid)
    )
    _CF.CFRelease(cf_type)
    _CF.CFRelease(cf_name)

    if rc != 0:
        _log.warning("power_assertion: IOPMAssertionCreateWithName rc=%d", rc)
        return False

    _assertion_id = aid
    _log.info("power_assertion: acquired (id=%d) name=%r", aid.value, name)
    return True


def release() -> None:
    """Release a previously acquired assertion. Idempotent."""
    global _assertion_id
    if _assertion_id is None or _IOKit is None:
        return
    rc = _IOKit.IOPMAssertionRelease(_assertion_id)
    if rc != 0:
        _log.warning("power_assertion: IOPMAssertionRelease rc=%d", rc)
    else:
        _log.info("power_assertion: released (id=%d)", _assertion_id.value)
    _assertion_id = None
