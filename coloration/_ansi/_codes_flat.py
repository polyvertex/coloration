# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

__all__ = []  # populated by _expose_ansi_codes()

_CODE_TO_NAME_MAP = {}  # populated by _expose_ansi_codes()


def _expose_ansi_codes():
    """
    This function takes all the values from the ``Ansi*`` enum classes and
    declare them as globals of this module, as well as their `str` and `bytes`
    variants.

    For instance, enum value `AnsiStyle.RESET` gets 3 variants of it declared as
    globals of this module, and added to ``__all__``:

    * ``RESET``, the enum value itself, derived from `enum.Enum`, so it can be
      `enum.IntEnum` for instance
    * ``RESET_STR`` (`str`), which is a shorthand for
      `AnsiStyle.RESET.str_sequence`
    * ``RESET_BIN`` (`bytes`), a shorthand for `AnsiStyle.RESET.bin_sequence`

    Enum classes flattened by this function:

    * `AnsiEscape`
    * `AnsiControl` (names are prefixed with ``CONTROL_``)
    * `AnsiStyle`
    * `AnsiStdFore` (names are prefixed with ``STD_``)
    * `AnsiStdBack` (names are prefixed with ``STD_BG_``)
    * `AnsiFore8`
    * `AnsiBack8` (names are prefixed with ``BG_``)
    * `AnsiFore8Index`
    * `AnsiBack8Index`
    """
    import enum
    from . import _codes

    glbls = globals()

    def _declare_enum_value(name, value):
        assert isinstance(value, enum.Enum)
        key = id(value)  # CAUTION: ansi_code_to_global_name() relies on this
        assert key not in _CODE_TO_NAME_MAP
        _CODE_TO_NAME_MAP[key] = name

    def _declare_global(name, value):
        assert name not in glbls
        assert name not in __all__
        glbls[name] = value
        __all__.append(name)

    def _declare_enum(enum_class, *, prefix):
        # CAUTION: enums must be iterated using attribute __members__ since it
        # includes enum aliases (i.e. identical values with different names)
        for name, value in enum_class.__members__.items():
            if not name.startswith("_"):
                flat_name = f"{prefix}{name}"
                _declare_enum_value(flat_name, value)
                _declare_global(f"{flat_name}", value)
                _declare_global(f"{flat_name}_STR", value.str_sequence)
                _declare_global(f"{flat_name}_BIN", value.bin_sequence)

    _declare_enum(_codes.AnsiEscape, prefix="")
    _declare_enum(_codes.AnsiControl, prefix="CONTROL_")
    _declare_enum(_codes.AnsiStyle, prefix="")
    _declare_enum(_codes.AnsiStdFore, prefix="STD_")
    _declare_enum(_codes.AnsiStdBack, prefix="STD_BG_")
    _declare_enum(_codes.AnsiFore8, prefix="")
    _declare_enum(_codes.AnsiBack8, prefix="BG_")
    _declare_enum(_codes.AnsiFore8Index, prefix="")
    _declare_enum(_codes.AnsiBack8Index, prefix="")


_expose_ansi_codes()
del _expose_ansi_codes
