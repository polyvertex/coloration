# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import re

from . import _codes_flat
from ._codes import (
    AnsiCode,
    AnsiEscape,
    AnsiSGRType,
    AnsiStyle,
    AnsiColorType, AnsiForeColorType, AnsiBackColorType,
    AnsiStdFore, AnsiStdBack,
    AnsiFore8, AnsiForeRgb)
from ._codes_flat import (
    _CODE_TO_NAME_MAP, CSI_BIN, CSI_STR, RESET_BIN, RESET_STR)
from ._constants import (
    ANSI_ENCODING, ANSI_ENCODING_ERRORS,
    ANSI_CODE_REGEX_STR, ANSI_CODE_REGEX_BIN,
    ANSI_NONRESET_SGR_REGEX_STR, ANSI_NONRESET_SGR_REGEX_BIN,
    ANSI_AUTORESET_REGEX_BIN, ANSI_AUTORESET_REGEX_STR,
    ANSI_8BIT_COLOR_NAMES)


def ansi_autoreset(data):
    """
    Append a `AnsiStyle.RESET` sequence to *data* only if it is non-empty, and a
    `AnsiEscape.CSI` was found in it.

    Note that in case there are trailing ``\\n`` and/or ``\\r`` characters, the
    `AnsiStyle.RESET` sequence is inserted right in front of then so to avoid
    visual artifacts.

    Return *data* modified or unmodified.
    """
    if not data:
        return data

    try:
        if not ANSI_NONRESET_SGR_REGEX_STR.search(data):
            return data
    except TypeError:
        try:
            if not ANSI_NONRESET_SGR_REGEX_BIN.search(data):
                return data
        except TypeError:
            raise ValueError("data")
        else:
            repl = RESET_BIN + br"\1"
            regex = ANSI_AUTORESET_REGEX_BIN
    else:
        repl = RESET_STR + r"\1"
        regex = ANSI_AUTORESET_REGEX_STR

    return regex.sub(repl, data, count=1)


def ansi_code_to_global_name(ansi_code):
    """
    From a given `AnsiCode` object (enum value), return its global name as given
    by *coloration*, such that ``coloration.<resulting_name>`` always gives back
    *ansi_code*.
    """
    if not isinstance(ansi_code, AnsiCode):
        raise ValueError(f"ansi_code type: {type(ansi_code)}")
    key = id(ansi_code)  # as converted by _flatten_ansi_codes()
    return _CODE_TO_NAME_MAP[key]


_COLOR_REGEX = re.compile(
    r"""
        \A\s*
        (?:
            (?:
                \#?
                (?P<hexr>[a-fA-F0-9]{2})
                (?P<hexg>[a-fA-F0-9]{2})
                (?P<hexb>[a-fA-F0-9]{2})
            )
            |
            (?:
                (?P<idx>[0-9]+)
            )
            |
            (?:
                (?P<name>[a-zA-Z][a-zA-Z0-9_]+?)
                (?:_[Ss][Tt][Rr]|_[Bb][Ii][Nn])?
            )
        )
        \s*\Z
    """,
    re.A | re.VERBOSE)


def ansi_color(color, green=None, blue=None):
    """
    Convert any kind of color supported by *coloration* into an `AnsiCode`
    derived object suitable for *coloration* features.

    If 3 components are provided (*color*, *green* and *blue*), they are assumed
    to be `int` values in ``[0,255]``.

    If only *color* is provided, it can be:

    * A color name from the 8-bit palette
    * A color index from the 8-bit palette (i.e. `int` value in ``[0,255]``)
    * An HTML-like hex color value of format ``#rrggbb`` or ``rrggbb``
    * The name of a color, as exposed by *coloration* already, like ``STD_RED``

    This function returns the foreground variant of a given color by default,
    unless its background name has been provided via *color*.

    You can convert a foreground color to its background counterpart with
    ``back = fore.to_back()``. Note this expression returns *fore* if it was a
    background color already, such that you can blindly call it without
    preliminary test if you do require a background color.
    """
    def _color8(idx):
        # use the named variant (i.e. AnsiFore8 instead of AnsiFore8Index),
        # such that caller can get its name too if desired
        return AnsiFore8[ANSI_8BIT_COLOR_NAMES[idx]]

    if green is None and blue is None:
        if isinstance(color, int):
            # here, color is assumed to be the index of the 8-bit color palette
            if 0 <= color <= 255:
                return _color8(color)

            raise ValueError("color")
        else:
            if not color:
                raise ValueError("empty color")
            elif isinstance(color, (bytes, bytearray)):
                try:
                    color = color.decode(ANSI_ENCODING, ANSI_ENCODING_ERRORS)
                except UnicodeError:
                    raise ValueError("color")
            elif not isinstance(color, str):
                raise ValueError(f"color value type: {type(color)}")

            rem = _COLOR_REGEX.fullmatch(color)
            if not rem:
                raise ValueError("color")

            if rem["hexr"]:
                # color is an html-like hex color
                return AnsiForeRgb(
                    int(rem["hexr"], base=16),
                    int(rem["hexg"], base=16),
                    int(rem["hexb"], base=16))
            elif rem["idx"]:
                # color is a stringified version of an 8-bit index
                color_idx = int(color, base=10)
                if 0 <= color_idx <= 255:
                    return _color8(color_idx)
            elif rem["name"]:
                colname = rem["name"].upper()

                # is this the name of an existing AnsiCode?
                try:
                    code = getattr(_codes_flat, colname)
                except AttributeError:
                    pass
                else:
                    # safety check: ensure the code we got really is a color,
                    # since this function is not meant to be a proxy
                    # to _codes_flat module
                    if not isinstance(code, AnsiColorType):
                        raise ValueError(f"not a color code: {color}")
                    return code

            raise ValueError("color")
    else:
        for elem in (color, green, blue):
            if not isinstance(elem, int):
                raise ValueError(f"color compound type: {type(elem)}")
            elif not 0 <= elem <= 255:
                raise ValueError("color compound out of boundaries")

        return AnsiForeRgb(color, green, blue)


def ansi_decode(data):
    """
    Decode a *data* (`bytes`, `bytearray`, or `re.Pattern`) to a `str` object if
    not decoded already.

    If *data* is a `re.Pattern`, it is re-compiled with the same flags and a
    decoded pattern, only if pattern was not a `str` already.

    with decoded pattern is returned if *data* is a
    `re.Pattern`.

    This function decodes *data* with encoding `ANSI_ENCODING` and
    `ANSI_ENCODING_ERRORS`, since *data* is assumed to contain ANSI escape
    sequence(s) only.
    """
    if not data:
        assert isinstance(data, (str, bytes, bytearray, re.Pattern))
        return ""
    elif isinstance(data, (bytes, bytearray)):
        return data.decode(ANSI_ENCODING, ANSI_ENCODING_ERRORS)
    elif isinstance(data, str):
        return data
    elif isinstance(data, re.Pattern):
        if isinstance(data.pattern, bytes):
            pattern = data.pattern.decode(ANSI_ENCODING, ANSI_ENCODING_ERRORS)
            return re.compile(pattern, flags=data.flags)
        elif isinstance(data.pattern, str):
            return data
        else:
            raise ValueError(f"unknown re.Pattern pattern type {type(data)}")
    else:
        raise ValueError(f"data value type {type(data)}")


def ansi_encode(data):
    """
    Encode *data* (`str` or `re.Pattern`) to a `bytes` object if not already.

    If *data* is a `re.Pattern`, it is re-compiled with the same flags and an
    encoded pattern, only if pattern was not a `bytes` object already.

    This function encodes *data* with encoding `ANSI_ENCODING` and
    `ANSI_ENCODING_ERRORS`, since *data* is assumed to contain ANSI escape
    sequence(s) only.
    """
    if not data:
        assert isinstance(data, (str, bytes, bytearray, re.Pattern))
        return b""
    elif isinstance(data, str):
        return data.encode(ANSI_ENCODING, ANSI_ENCODING_ERRORS)
    elif isinstance(data, bytes):
        return data
    elif isinstance(data, bytearray):
        return bytes(data)
    elif isinstance(data, re.Pattern):
        if isinstance(data.pattern, str):
            pattern = data.pattern.encode(ANSI_ENCODING, ANSI_ENCODING_ERRORS)
            return re.compile(pattern, flags=data.flags)
        elif isinstance(data.pattern, bytes):
            return data
        else:
            raise ValueError(f"unknown re.Pattern pattern type {type(data)}")
    else:
        raise ValueError(f"data value type {type(data)}")


_JOINFLAG_NONE = 0x00
_JOINFLAG_FGCOL = 0x01
_JOINFLAG_BGCOL = 0x02
_JOINFLAG_STYLE = 0x04


def ansi_join(
        *codes, binary=False, autostr=True, autoreset=False,
        encoding="utf-8", errors="strict"):
    """
    Join multiple objects altogether in a single `str` or `bytes` sequence,
    depending on *binary* boolean.

    This function supports `AnsiCode` derived codes by accumulating them when
    possible (i.e. `AnsiSGRType` derived codes can be accumulated in a single
    ANSI escape sequence), so it is recommended to pass them as enum values
    instead of already converted `str` or `bytes` values.

    Every *codes* value can be either an `AnsiCode` value, or a `str` object, or
    a `bytes` or `bytearray` object.

    If *autostr* is disabled (enabled by default), only `AnsiCode`, `str`,
    `byte`, and `bytearray` objects are supported. If enabled, all other types
    of objects are supported via a cast to `str` first (then converted to
    `bytes` if needed).

    If *binary* is true, passed `str` objects are encoded using *encoding* and
    *errors* arguments if specified (passed as-is to `str.encode`).

    The same logic applies to passed `bytes` objects, which get decoded
    if *binary* is false.

    *autoreset* can be enabled so to automatically rollback coloring and
    styling. Note that, unlike `ansi_autoreset`, this is a more fine-grained
    approach that tries to reset only the attributes that changed (i.e.
    foreground color, background color, or whole styling).
    """
    def _flush_sgr():
        if accumulated_sgr:
            joined.extend((csi, semicolon.join(accumulated_sgr), m_suffix))
            accumulated_sgr.clear()

    def _autoreset_append(value):
        nonlocal reset_flags
        if autoreset and not (reset_flags & _JOINFLAG_STYLE) and csi in value:
            reset_flags |= _JOINFLAG_STYLE
        joined.append(value)

    binary = bool(binary)
    autostr = bool(autostr)
    autoreset = bool(autoreset)

    if binary:
        empty = b""
        semicolon = b";"
        m_suffix = b"m"
        csi = CSI_BIN
    else:
        empty = ""
        semicolon = ";"
        m_suffix = "m"
        csi = CSI_STR

    accumulated_sgr = []
    joined = []
    reset_flags = _JOINFLAG_NONE

    for item in codes:
        if isinstance(item, AnsiSGRType):
            item_value = item.bin_value if binary else item.str_value
            accumulated_sgr.append(item_value)
            if autoreset:
                if item is AnsiStyle.RESET:
                    reset_flags = _JOINFLAG_NONE
                elif item is AnsiStdFore.DEFAULT:
                    reset_flags &= ~_JOINFLAG_FGCOL
                elif item is AnsiStdBack.DEFAULT:
                    reset_flags &= ~_JOINFLAG_BGCOL
                elif isinstance(item, AnsiForeColorType):
                    reset_flags |= _JOINFLAG_FGCOL
                elif isinstance(item, AnsiBackColorType):
                    reset_flags |= _JOINFLAG_BGCOL
                else:
                    reset_flags |= _JOINFLAG_STYLE
        elif isinstance(item, AnsiCode):
            _flush_sgr()
            item = item.bin_sequence if binary else item.str_sequence
            joined.append(item)
        elif isinstance(item, str):
            _flush_sgr()
            if binary:
                item = item.encode(encoding, errors)
            _autoreset_append(item)
        elif isinstance(item, (bytes, bytearray)):
            _flush_sgr()
            if not binary:
                item = item.decode(encoding, errors)
            _autoreset_append(item)
        elif not autostr:
            raise ValueError(f"item type {type(item)}")
        else:
            _flush_sgr()
            item_value = str(item)
            if binary:
                item_value = item_value.encode(encoding, errors)
            _autoreset_append(item)

    if autoreset and reset_flags != _JOINFLAG_NONE:
        if reset_flags & _JOINFLAG_STYLE:
            code = RESET_BIN if binary else RESET_STR
            accumulated_sgr.append(code)
        else:
            for flag, code in (
                    (_JOINFLAG_FGCOL, AnsiStdFore.DEFAULT),
                    (_JOINFLAG_BGCOL, AnsiStdBack.DEFAULT)):
                if reset_flags & flag:
                    accumulated_sgr.append(
                        code.bin_value if binary else code.str_value)

    _flush_sgr()

    return empty.join(joined)


def ansi_strip(data):
    """
    Remove all ANSI Control sequences (CSI) and Operating System commands (OSC)
    found in *data*, then return the modified version of *data*
    """
    if not data:
        return data

    try:
        return ANSI_CODE_REGEX_STR.sub("", data)
    except TypeError:
        try:
            return ANSI_CODE_REGEX_BIN.sub(b"", data)
        except TypeError:
            raise ValueError("data")


def ansi_title(title):
    """
    Build and return a `str` or `bytes` ANSI sequence (depending on the type of
    *title*), that allows to change terminal's title.

    The returned sequence can be written directly to a file.
    """
    if isinstance(title, str):
        return "".join((
            AnsiEscape.OSC.str_value,
            "0;",  # can be 0, 1, or 2
            title,
            AnsiEscape.BEL.str_value))
    elif isinstance(title, (bytes, bytearray)):
        return b"".join((
            AnsiEscape.OSC.bin_value,
            b"0;",  # can be 0, 1, or 2
            title,
            AnsiEscape.BEL.bin_value))
    else:
        raise ValueError("title")
