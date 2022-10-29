# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import re

from ._highlighter import Highlighter
from ._repl import (
    HighlighterRepl,
    HighlighterPreparedRepl,
    HighlighterPreparedReplBin,
    HighlighterPreparedReplStr)
from ._span import HighlighterSpan, HighlighterRegion
from .._ansi import ansi_decode, ansi_encode


class RegexHighlighter(Highlighter):
    """Base abstract class for automatic regex-based text highlighting"""

    Repl = HighlighterRepl

    _highlights_ = ()
    _highlights_repl_ = {}
    _assert_unoptimized_regex_ = True

    def __init__(self, *, binary=False):
        super().__init__()

        binary = bool(binary)

        if binary:
            regex_convert = ansi_encode
            repl_class = HighlighterPreparedReplBin
        else:
            regex_convert = ansi_decode
            repl_class = HighlighterPreparedReplStr

        regexes = []
        for regex in self._highlights_:
            if not isinstance(regex, re.Pattern):
                raise ValueError(f"regex expected; got type {type(regex)}")
            regexes.append(regex_convert(regex))

        repls = {}
        for repl_name, repl_value in self._highlights_repl_.items():
            if not isinstance(repl_value, HighlighterRepl):
                raise ValueError(f"regex expected; got type {type(repl_value)}")
            repls[repl_name] = repl_class(repl_value)

        self._is_binary = binary
        self._regexes = tuple(regexes)
        self._repls = repls
        self._empty = repl_class.EMPTY

    @property
    def is_binary(self):
        """A `bool` value to indicate `bytes` or `str` streams support"""
        return self._is_binary

    def highlight(self, data):
        def _do_repl(region, match):
            empty_match = True
            prev_end = 0

            for match_name, match_value in match.groupdict().items():
                if match_value is None:
                    continue  # empty match

                mstart, mend = match.span(match_name)
                if mstart < prev_end:
                    continue  # this part already matched

                # TEST
                # print(
                #     f"_HLMATCH_ <{match_name} [{mstart}:{mend}]> "
                #     f"{match_value!r}")

                try:
                    repl = self._repls[match_name]
                except KeyError:
                    repl = self._repls.get(None, self._empty)

                assert isinstance(repl, HighlighterPreparedRepl)
                repl = repl.replace_with(match_value)

                region.insert_span(HighlighterSpan(mstart, mend, repl))
                empty_match = False
                prev_end = mend

            # reaching this assertion means the regex is not optimized as it
            # allows empty matches, which means this function will be called
            # much more often, for every character in the worst case, looping in
            # match.groupdict() every time
            if __debug__:
                if empty_match and self._assert_unoptimized_regex_:
                    raise AssertionError("unoptimized regex")

        if not data:
            return self._empty
        elif not self._is_binary:
            if not isinstance(data, str):
                raise ValueError(f"expected str data; got {type(data)}")
        elif not isinstance(data, bytes):
            raise ValueError(f"expected bytes data; got {type(data)}")

        region = HighlighterRegion(0, len(data))

        for regex in self._regexes:
            for span in region:
                if span.data is None:  # this part did not match a regex already
                    for match in regex.finditer(data, span.start, span.end):
                        _do_repl(region, match)

        result = []
        for span in region:
            if span.data is None:
                res = data[span.start:span.end]
            else:
                res = span.data
            result.append(res)

        result = self._empty.join(result)
        return result
