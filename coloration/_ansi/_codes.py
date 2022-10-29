# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import enum

from ._constants import ANSI_ENCODING, ANSI_ENCODING_ERRORS, ANSI_8BIT_COLOR_NAMES


class AnsiCode:
    """
    Base class for every ANSI code enums and classes defined in this module
    (`ref. <https://en.wikipedia.org/wiki/ANSI_escape_code>`_)
    """
    __slots__ = ()

    def __str__(self):
        return self.str_value

    def __getattr__(self, name):
        if name == "str_value":
            value = str(self.value)
            setattr(self, name, value)
            return value

        if name == "bin_value":
            value = self.str_value.encode(ANSI_ENCODING, ANSI_ENCODING_ERRORS)
            setattr(self, name, value)
            return value

        if name == "str_sequence":
            value = self._build_sequence()
            setattr(self, name, value)
            return value

        if name == "bin_sequence":
            value = self.str_sequence.encode(ANSI_ENCODING, ANSI_ENCODING_ERRORS)
            setattr(self, name, value)
            return value

        raise AttributeError(name)

    def _build_sequence(self):
        return self.str_value


class AnsiDynCode(AnsiCode):
    """
    Like `AnsiCode` (and derived from it), except it is meant to be used to
    build *dynamic* ANSI escape sequences, that take parameters in like for
    instance ``ESC[38;2;<r>;<g>;<b>``, which requires 3 arguments.

    .. seealso:: `AnsiForeRgb` and `AnsiBackRgb`
    """

    __slots__ = ("_str_value", "bin_value", "str_sequence", "bin_sequence")

    def __init__(self, str_value):
        assert isinstance(str_value, str)
        assert str_value
        self._str_value = str_value

    def __str__(self):
        return self._str_sequence

    @property
    def value(self):  # needed by AnsiCode.__getattr__()
        return self._str_value

    @property
    def str_value(self):
        return self._str_value


class AnsiSGRType:
    """
    Mixin class for ANSI Select Graphic Rendition sequences.

    Do not instantiate directly.
    """
    __slots__ = ()

    def _build_sequence(self):
        return "{}{}m".format(
            AnsiEscape.CSI.str_value,
            self.str_value)


class AnsiColorType:
    """
    Mixin class for colors.

    Do not instantiate directly.

    .. seealso:: `AnsiRgbColorType`, `AnsiForeColorType`, `AnsiBackColorType`
    """
    __slots__ = ()


class AnsiStdColorType:
    """
    Mixin class for standard 4-bit colors.

    Do not instantiate directly.
    """
    __slots__ = ()


class Ansi8bitColorType:
    """
    Mixin class for 8-bit colors (palette).

    Do not instantiate directly.
    """
    __slots__ = ()

    def __getattr__(self, name):
        if name == "str_value":
            value = "38" if isinstance(self, AnsiForeColorType) else "48"
            value = f"{value};5;{self.value}"
            # pylint: disable=assigning-non-slot, attribute-defined-outside-init
            self.str_value = value
            return value

        return AnsiCode.__getattr__(self, name)


class AnsiRgbColorType:
    """
    Mixin class for RGB (24-bit) colors.

    Do not instantiate directly.
    """
    __slots__ = ()


class AnsiForeColorType:
    """
    Mixin class for any type of foreground colors.

    Do not instantiate directly.

    .. seealso:: `AnsiBackColorType`, `AnsiColorType`
    """
    __slots__ = ()

    def to_fore(self):
        """
        Return this color's foreground counterpart, or return *self* if this
        color is already foreground.
        """
        return self

    def to_back(self):
        """
        Return this color's background counterpart, or return *self* if this
        color is already background.
        """
        raise NotImplementedError


class AnsiBackColorType:
    """
    Mixin class for any type of background colors.

    Do not instantiate directly.

    .. seealso:: `AnsiForeColorType`, `AnsiColorType`
    """
    __slots__ = ()

    def to_fore(self):
        """
        Return this color's foreground counterpart, or return *self* if this
        color is already foreground.
        """
        raise NotImplementedError

    def to_back(self):
        """
        Return this color's background counterpart, or return *self* if this
        color is already background.
        """
        return self


class AnsiEscape(AnsiCode, enum.Enum):
    """ANSI escape sequences"""

    SOH = "\001"
    CSI = "\033["  #: Control Sequence Introducer
    OSC = "\033]"  #: Operating System Command
    BEL = "\007"  #: Bell ANSI character (or ``\\a``)
    STX = "\002"


class AnsiControl(AnsiCode, enum.Enum):
    """
    Some ANSI control codes related to screen and line erasing, showing/hiding
    cursor, enabling/disabling alternative screen buffer, ...
    """

    #: RIS; triggers a full reset of the terminal to its original state
    FULL_TERM_RESET = "\033c"

    CLEAR_SCREEN_FROM_CURSOR = "\033[0J"
    CLEAR_SCREEN_TO_CURSOR = "\033[1J"
    CLEAR_SCREEN = "\033[2J"
    CLEAR_SCREEN_AND_SCROLLBACK = "\033[3J"

    CLEAR_LINE_FROM_CURSOR = "\033[0K"
    CLEAR_LINE_TO_CURSOR = "\033[1K"
    CLEAR_LINE = "\033[2K"

    SHOW_CURSOR = "\033[?25h"
    HIDE_CURSOR = "\033[?25l"

    ENABLE_ALT_SCREEN = "\033[?1049h"
    DISABLE_ALT_SCREEN = "\033[?1049l"

    MOVE_TO_TOPLEFT = "\033[H"

    @staticmethod
    def cursor_up(lines=1):
        """Move cursor up"""
        assert isinstance(lines, int)
        assert lines >= 0
        return AnsiDynCode(f"\033[{lines}A")

    @staticmethod
    def cursor_down(lines=1):
        """Move cursor down"""
        assert isinstance(lines, int)
        assert lines >= 0
        return AnsiDynCode(f"\033[{lines}B")

    @staticmethod
    def cursor_forward(columns=1):
        """Move cursor forward"""
        assert isinstance(columns, int)
        assert columns >= 0
        return AnsiDynCode(f"\033[{columns}C")

    @staticmethod
    def cursor_backward(columns=1):
        """Move cursor backward"""
        assert isinstance(columns, int)
        assert columns >= 0
        return AnsiDynCode(f"\033[{columns}D")

    @staticmethod
    def move_to_x(x=0):
        """Move cursor to column *x*"""
        assert isinstance(x, int)
        assert x >= 0
        return AnsiDynCode(f"\033[{x+1}G")

    @staticmethod
    def move_to_xy(x=0, y=0):
        """Move cursor to column *x* and row *y*"""
        assert isinstance(x, int)
        assert x >= 0
        assert isinstance(y, int)
        assert y >= 0
        return AnsiDynCode(f"\033[{y+1};{x+1}H")


class AnsiStyle(AnsiSGRType, AnsiCode, enum.IntEnum):
    """ANSI Select Graphic Rendition attributes"""

    RESET = 0
    BOLD = 1  # increased intensity
    DIM = 2  # decreased intensity
    ITALIC = 3
    UNDERLINE = 4
    BLINK = 5
    RAPIDBLINK = 6
    INVERSE = 7
    CONCEAL = 8
    STRIKE = 9
    NORMAL = 22  # normal intensity
    REVEAL = 28  # conceal off


class AnsiStdFore(
        AnsiForeColorType,
        AnsiStdColorType,
        AnsiColorType,
        AnsiSGRType,
        AnsiCode,
        enum.IntEnum):
    """ANSI standard foreground colors"""

    DEFAULT = 39

    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37

    # bright colors (non-standard)
    LIGHTBLACK = 90
    LIGHTRED = 91
    LIGHTGREEN = 92
    LIGHTYELLOW = 93
    LIGHTBLUE = 94
    LIGHTMAGENTA = 95
    LIGHTCYAN = 96
    LIGHTWHITE = 97

    def to_back(self):
        return AnsiStdBack[self.name]


class AnsiStdBack(
        AnsiBackColorType,
        AnsiStdColorType,
        AnsiColorType,
        AnsiSGRType,
        AnsiCode,
        enum.IntEnum):
    """ANSI standard background colors"""

    DEFAULT = 49

    BLACK = 40
    RED = 41
    GREEN = 42
    YELLOW = 43
    BLUE = 44
    MAGENTA = 45
    CYAN = 46
    WHITE = 47

    # bright colors (non-standard)
    LIGHTBLACK = 100
    LIGHTRED = 101
    LIGHTGREEN = 102
    LIGHTYELLOW = 103
    LIGHTBLUE = 104
    LIGHTMAGENTA = 105
    LIGHTCYAN = 106
    LIGHTWHITE = 107

    def to_fore(self):
        return AnsiStdFore[self.name]


class AnsiFore8(
        AnsiForeColorType,
        Ansi8bitColorType,
        AnsiColorType,
        AnsiSGRType,
        AnsiCode,
        enum.IntEnum):
    """
    ANSI foreground 8-bit colors palette, by name.

    This enumerates all the 256 8-bit colors by name, using list
    `ANSI_8BIT_COLOR_NAMES`.
    """

    # automagically generate enum values
    _ignore_ = "_idx _nam"
    for _idx, _nam in enumerate(ANSI_8BIT_COLOR_NAMES):
        vars()[_nam] = _idx

    def __getattr__(self, name):
        return Ansi8bitColorType.__getattr__(self, name)

    def to_back(self):
        return AnsiBack8[self.name]


class AnsiBack8(
        AnsiBackColorType,
        Ansi8bitColorType,
        AnsiColorType,
        AnsiSGRType,
        AnsiCode,
        enum.IntEnum):
    """
    ANSI background 8-bit colors palette, by name.

    This enumerates all the 256 8-bit colors by name, using list
    `ANSI_8BIT_COLOR_NAMES`.
    """

    # automagically generate enum values
    _ignore_ = "_idx _nam"
    for _idx, _nam in enumerate(ANSI_8BIT_COLOR_NAMES):
        vars()[_nam] = _idx

    def __getattr__(self, name):
        return Ansi8bitColorType.__getattr__(self, name)

    def to_fore(self):
        return AnsiFore8[self.name]


class AnsiFore8Index(
        AnsiForeColorType,
        Ansi8bitColorType,
        AnsiColorType,
        AnsiSGRType,
        AnsiCode,
        enum.IntEnum):
    """
    ANSI foreground 8-bit colors palette, by index.

    This enumerates all the 256 8-bit colors, named after their respective index
    from ``FG8_0`` to ``FG8_255``.
    """

    # automagically generate enum values
    _ignore_ = "_idx"
    for _idx in range(len(ANSI_8BIT_COLOR_NAMES)):
        vars()[f"FG8_{_idx}"] = _idx

    def __getattr__(self, name):
        return Ansi8bitColorType.__getattr__(self, name)

    def to_back(self):
        return AnsiBack8Index[f"BG8_{self.value}"]

    @classmethod
    def from_index(cls, color_index):
        try:
            return cls[f"FG8_{color_index}"]
        except KeyError:
            pass

        if not isinstance(color_index, int) or isinstance(color_index, bool):
            raise ValueError(f"8-bit color index value type {type(color_index)}")

        raise ValueError(f"8-bit color index out of bounds: {color_index}")


class AnsiBack8Index(
        AnsiBackColorType,
        Ansi8bitColorType,
        AnsiColorType,
        AnsiSGRType,
        AnsiCode,
        enum.IntEnum):
    """
    ANSI background 8-bit colors palette, by index.

    This enumerates all the 256 8-bit colors, named after their respective index
    from ``BG8_0`` to ``BG8_255``.
    """

    # automagically generate enum values
    _ignore_ = "_idx"
    for _idx in range(len(ANSI_8BIT_COLOR_NAMES)):
        vars()[f"BG8_{_idx}"] = _idx

    def __getattr__(self, name):
        return Ansi8bitColorType.__getattr__(self, name)

    def to_fore(self):
        return AnsiFore8Index[f"FG8_{self.value}"]

    @classmethod
    def from_index(cls, color_index):
        try:
            return cls[f"BG8_{color_index}"]
        except KeyError:
            pass

        if not isinstance(color_index, int) or isinstance(color_index, bool):
            raise ValueError(f"8-bit color index value type {type(color_index)}")

        raise ValueError(f"8-bit color index out of bounds: {color_index}")


class AnsiForeRgb(
        AnsiForeColorType,
        AnsiRgbColorType,
        AnsiColorType,
        AnsiSGRType,
        AnsiDynCode):
    """
    A dynamic ANSI escape code to represent a foreground RBG color (24-bit)
    """
    __slots__ = ()

    def __init__(self, red, green, blue):
        assert isinstance(red, int)
        assert isinstance(green, int)
        assert isinstance(blue, int)
        assert 0 <= red <= 255
        assert 0 <= green <= 255
        assert 0 <= blue <= 255
        AnsiDynCode.__init__(self, f"38;2;{red};{green};{blue}")

    def to_back(self):
        red, green, blue = map(int, self.str_value.split(";")[2:5])
        return AnsiBackRgb(red, green, blue)


class AnsiBackRgb(
        AnsiBackColorType,
        AnsiRgbColorType,
        AnsiColorType,
        AnsiSGRType,
        AnsiDynCode):
    """
    A dynamic ANSI escape code to represent a background RBG color (24-bit)
    """
    __slots__ = ()

    def __init__(self, red, green, blue):
        assert isinstance(red, int)
        assert isinstance(green, int)
        assert isinstance(blue, int)
        assert 0 <= red <= 255
        assert 0 <= green <= 255
        assert 0 <= blue <= 255
        AnsiDynCode.__init__(self, f"48;2;{red};{green};{blue}")

    def to_fore(self):
        red, green, blue = map(int, self.str_value.split(";")[2:5])
        return AnsiForeRgb(red, green, blue)
