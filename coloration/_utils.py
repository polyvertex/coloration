# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import atexit
import os
import sys


def enable_windows_vt100(*, stdout=True, stderr=True, raise_errors=False):
    """
    Enable `VT100 emulation
    <https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences>`_
    on current Windows console if needed.

    This has no effect if ``sys.platform != "win32"`` (this test discards
    cygwin), or if VT100 emulation is already enabled.

    Return an `int` value:

    * ``0`` in case VT100 emulation could not be enabled (i.e. not supported)
    * ``1`` if operation succeeded for at least stdout or stderr
    * ``2`` if operation succeeded for both handles

    Raise `OSError` upon error and if *raise_errors* is true (false by default).

    Note that VT100 emulation is enabled by default starting with Windows 10
    build 1909.
    """
    assert isinstance(stdout, bool)
    assert isinstance(stderr, bool)
    assert isinstance(raise_errors, bool)
    assert stdout or stderr

    if sys.platform != "win32":
        return 0  # cygwin case falls here as well

    import ctypes
    import ctypes.wintypes

    STD_OUTPUT_HANDLE = ctypes.wintypes.DWORD(-11).value
    STD_ERROR_HANDLE = ctypes.wintypes.DWORD(-12).value
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    INVALID_HANDLE_VALUE = ctypes.wintypes.HANDLE(-1).value

    GetLastError = ctypes.windll.kernel32.GetLastError
    GetLastError.restype = ctypes.wintypes.DWORD
    GetLastError.argtypes = []

    GetStdHandle = ctypes.windll.kernel32.GetStdHandle
    GetStdHandle.restype = ctypes.wintypes.HANDLE
    GetStdHandle.argtypes = [ctypes.wintypes.DWORD]

    GetConsoleMode = ctypes.windll.kernel32.GetConsoleMode
    GetConsoleMode.restype = ctypes.wintypes.BOOL
    GetConsoleMode.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.LPDWORD]

    SetConsoleMode = ctypes.windll.kernel32.SetConsoleMode
    SetConsoleMode.restype = ctypes.wintypes.BOOL
    SetConsoleMode.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD]

    def _enable_vt100(std_handle_id):
        handle = GetStdHandle(std_handle_id)
        if handle == INVALID_HANDLE_VALUE:
            if raise_errors:
                raise OSError(
                    0, f"GetStdHandle({std_handle_id}) failed", None,
                    GetLastError())
            return False

        dwOrigMode = ctypes.wintypes.DWORD(0)
        if not GetConsoleMode(handle, ctypes.byref(dwOrigMode)):
            error = GetLastError()
            if error == 6:  # ERROR_INVALID_HANDLE
                # occurs when handle is not associated to a console
                return False
            if raise_errors:
                raise OSError(
                    0, f"GetConsoleMode({std_handle_id}) failed", None,
                    error)
            return False

        dwOrigMode = dwOrigMode.value
        if not dwOrigMode & ENABLE_VIRTUAL_TERMINAL_PROCESSING:
            if not SetConsoleMode(
                    handle, dwOrigMode | ENABLE_VIRTUAL_TERMINAL_PROCESSING):
                if raise_errors:
                    raise OSError(
                        0, f"SetConsoleMode({std_handle_id}) failed", None,
                        GetLastError())
                return False

        return True

    stdout_res = _enable_vt100(STD_OUTPUT_HANDLE) if stdout else 0
    stderr_res = _enable_vt100(STD_ERROR_HANDLE) if stderr else 0

    return int(stderr_res) + int(stdout_res)


def is_file_tty(file):
    """
    Return a `bool` to indicate whether *file* is a TTY.

    PyCharm supported.
    """
    # PYCHARM_HOSTED test from colorama
    if ("PYCHARM_HOSTED" in os.environ and (
            file is sys.__stdout__ or
            file is sys.__stderr__)):
        return True

    try:
        is_tty = file.isatty()
    except (AttributeError, TypeError):
        return False
    else:
        return bool(is_tty)


def is_file_writable(file):
    """
    Return a `bool` to indicate whether *file* is writable, by checking if it
    has a ``write()`` method, and also the return value of its ``writable``
    method (or property if not a callable) if any.
    """
    try:
        method = file.write
    except AttributeError:
        return False
    else:
        if not callable(method):
            return False

    try:
        method = file.writable
    except AttributeError:
        # do not be too strict and assume it is ok since file.write is a callable
        return True
    else:
        if not callable(method):
            return bool(method)
        return bool(method())


def unwrap_std_streams():
    """Revert the action of `wrap_std_streams()`"""
    from ._stream import ColorationStream

    # CAUTION: this code may be called from an atexit handler, so be extra
    # careful and do not take anything for granted regarding the availability
    # of some standard attributes, as well as their value

    for stream_name in ("stdout", "stderr"):
        try:
            stream = getattr(sys, stream_name)
        except AttributeError:
            # this may happen if this function is called from an atexit handler
            # for instance
            continue

        if isinstance(stream, ColorationStream):
            wrapped = stream.wrapped

            if wrapped is not None:
                # emit a RESET just in case and as long as escaping is enabled
                stream.reset_style()

                # make this wrapper an empty shell
                stream.detach()
            else:
                try:
                    wrapped = getattr(sys, f"__{stream_name}__")
                except AttributeError:
                    wrapped = None

            try:
                setattr(sys, stream_name, wrapped)
            except Exception:  # pylint: disable=broad-except
                pass

            del stream, wrapped


def wrap_std_streams(**colorstream_kwargs):
    """
    Wrap `std.stdout` and `std.stderr` streams with `ColorationStream` if not
    done already.

    You may want to call `enable_windows_vt100()` before.

    .. seealso:: `unwrap_std_streams()`
    """
    from ._stream import ColorationStream

    for stream_name in ("stdout", "stderr"):
        orig_stream = getattr(sys, stream_name)
        if isinstance(orig_stream, ColorationStream):
            continue

        stream = ColorationStream(
            stream=orig_stream, acquire=False, **colorstream_kwargs)
        assert not stream.owns_wrapped
        setattr(sys, stream_name, stream)

    atexit.unregister(unwrap_std_streams)  # in case this is not the first time
    atexit.register(unwrap_std_streams)
