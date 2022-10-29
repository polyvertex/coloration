# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

from ._utils import enable_windows_vt100, unwrap_std_streams, wrap_std_streams


def init(*, wrap=True, **colorstream_kwargs):
    """
    This function provides a single entry-point for convenience, to:

    * Optionally call `wrap_std_streams()` (depending on *wrap*)
    * call `enable_windows_vt100()` in a no-error-raised fashion

    .. seealso:: `uninit`
    """
    enable_windows_vt100(stdout=True, stderr=True, raise_errors=False)
    if wrap:
        wrap_std_streams(**colorstream_kwargs)


def uninit():
    """
    Undo `init()`.

    For now this function just unwraps `sys.stdout` and `sys.stderr` if needed.

    .. seealso:: `init`
    """
    unwrap_std_streams()
