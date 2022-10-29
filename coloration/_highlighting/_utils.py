# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

from ._default import DefaultHighlighter
from ._highlighter import Highlighter

_default_highlighter_str = DefaultHighlighter(binary=False)
_default_highlighter_bin = DefaultHighlighter(binary=True)


def highlight(data):
    """
    Convenience function to highlight *data* using an internally instantiated
    `DefaultHighlighter`
    """
    if isinstance(data, str):
        return _default_highlighter_str(data)
    else:
        assert isinstance(data, (bytes, bytearray))
        return _default_highlighter_bin(data)


def select_highlighter(highlighter=None, /, *, binary=False, **kwargs):
    """
    Select the appropriate `Highlighter` depending on the value of
    *highlighter*.

    If *highlighter* is strictly `False`, `None` is returned.

    If *highlighter* is strictly `None` or `True`, an instance of
    `DefaultHighlighter` is returned.

    If *highlighter* is an (derived) instance of `Highlighter`, *highlighter* is
    returned.

    Raise a `ValueError` otherwise.
    """
    if highlighter is None or highlighter is True:
        if not kwargs:
            return (
                _default_highlighter_bin if binary
                else _default_highlighter_str)
        else:
            return DefaultHighlighter(binary=binary, **kwargs)
    elif highlighter is False:
        return None
    elif isinstance(highlighter, Highlighter):
        return highlighter
    else:
        raise ValueError(f"highlighter type: {type(highlighter)}")
