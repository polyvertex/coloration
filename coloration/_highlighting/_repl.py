# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import re

from .._ansi import AnsiCode, ansi_decode, ansi_encode, ansi_join

_DUMMY_REPL = ">#HL^REPL[{}]<"

_DUMMY_REPL_REGEX_STR = re.compile(r"\>#HL\^REPL\[([0-9]+)\]\<", flags=re.A)
_DUMMY_REPL_REGEX_BIN = re.compile(
    ansi_encode(_DUMMY_REPL_REGEX_STR.pattern),
    flags=_DUMMY_REPL_REGEX_STR.flags)


class HighlighterRepl:
    """
    A replacement sequence to be used by `Highlighter` objects.

    *sequence* can be empty in which case an empty value is returned during
    replacement.

    Otherwise, it works pretty much like `ansi_join()` where each element of
    *sequence* can be either:

    * Any `AnsiCode` instance or derived
    * A `str`, `bytes` or `bytearray` object
    * A non-signed `int` value, that will act as a placeholder to reference
      matched groups during replacement (see
      `HighlighterPreparedRepl.replace_with()`)

    *autoreset* has the same meaning than for `ansi_join()`.

    `HighlighterRepl` objects are automatically converted to
    `HighlighterPreparedRepl` objects by `Highlighter` when needed, in order to
    improve replacement speed.

    Examples:

    .. code-block:: python

        # always replace by match group 0
        HighlighterRepl(0)
        HighlighterRepl()  # same as previous line

        # special case: always replace by an empty value
        HighlighterRepl(None)

        # always replace by a concatenation of match groups 1 and 3
        HighlighterRepl(1, 3)

        # always replace by match group #1, colored in red
        HighlighterRepl(coloration.STD_RED, 1)

        # always replace by match group #1, colored in red, but do not reset
        # style afterward, meaning that any trailing data will also be colored
        # in red
        HighlighterRepl(coloration.STD_RED, 1, autoreset=False)

        # a more complex example, involving multiple styles and placeholders
        HighlighterRepl(
            coloration.STD_BLUE, 1,
            coloration.STD_GREEN, 2)
    """

    __slots__ = ("_sequence", "_autoreset")

    def __init__(self, *sequence, autoreset=True):
        self._sequence = sequence
        self._autoreset = autoreset

    def prepare(self, *, binary):
        # handle special cases
        if not self._sequence:
            return (0, )
        elif len(self._sequence) == 1 and self._sequence[0] is None:
            return (None, )

        result = []

        for item in self._sequence:
            if isinstance(item, AnsiCode):
                result.append(item)
            elif isinstance(item, str):
                if binary:
                    item = ansi_encode(item)
                result.append(item)
            elif isinstance(item, (bytes, bytearray)):
                if binary:
                    item = ansi_decode(item)
                result.append(item)
            elif isinstance(item, int):
                if isinstance(item, bool) or item < 0:
                    raise ValueError(
                        f"invalid replacement placeholder value: {item}")
                elif binary:
                    item = ansi_encode(_DUMMY_REPL.format(item))
                else:
                    item = _DUMMY_REPL.format(item)
                result.append(item)
            else:
                raise ValueError(
                    f"invalid replacement placeholder value type: "
                    f"{type(item)})")

        sequence = ansi_join(
            *result, binary=binary, autostr=False, autoreset=self._autoreset)
        result = []
        start = 0
        repl_regex = _DUMMY_REPL_REGEX_BIN if binary else _DUMMY_REPL_REGEX_STR

        while start < len(sequence):
            if not (rem := repl_regex.search(sequence, start)):
                result.append(sequence[start:])
                break

            mstart, mend = rem.span(0)
            if mstart > start:
                result.append(sequence[start:mstart])
            result.append(int(rem[1], base=10))
            start = mend

        return tuple(result)


class HighlighterPreparedRepl:
    """
    Base class for `HighlighterPreparedReplStr` and
    `HighlighterPreparedReplBin`. Not meant to be instanciated directly.
    """

    __slots__ = ("_repl", )

    IS_BINARY = None
    EMPTY = None

    def __init__(self, repl):
        # safety check the class-properties that must be overridden by the
        # derived class
        assert self.IS_BINARY is False or self.IS_BINARY is True
        assert isinstance(self.EMPTY, (str, bytes))
        assert not self.EMPTY

        if not isinstance(repl, HighlighterRepl):
            raise ValueError(f"HighlighterRepl expected; got {type(repl)}")

        repl = repl.prepare(binary=self.IS_BINARY)
        assert isinstance(repl, tuple)

        self._repl = repl

    def __call__(self, *args, **kwargs):
        return self.replace_with(*args, **kwargs)

    def replace_with(self, *repl):
        # special case
        if len(self._repl) == 1 and self._repl[0] is None:
            return self.EMPTY

        result = []

        for item in self._repl:
            if isinstance(item, int):
                try:
                    item = repl[item]
                except (IndexError, KeyError):
                    raise ValueError(
                        f"replacement placeholder index #{item} does not exist "
                        f"in input sequence (sequence length: {len(repl)})")
                else:
                    # silently rely on __str__ if item is not a string already
                    if not self.IS_BINARY and not isinstance(item, str):
                        item = str(item)

            result.append(item)

        try:
            result = self.EMPTY.join(result)
        except TypeError as exc:
            raise ValueError(
                f"input sequence may contains mixed types; error: {exc}")

        return result


class HighlighterPreparedReplBin(HighlighterPreparedRepl):
    """Same as `HighlighterPreparedReplStr` for `bytes` streams"""

    __slots__ = ()

    IS_BINARY = True
    EMPTY = b""


class HighlighterPreparedReplStr(HighlighterPreparedRepl):
    """
    A *prepared* version of `HighlighterRepl` for `str` streams.

    Note that `HighlighterPreparedRepl` instances are NOT derived from
    `HighlighterRepl`.
    """

    __slots__ = ()

    IS_BINARY = False
    EMPTY = ""
