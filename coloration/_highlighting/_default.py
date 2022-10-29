# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import re

from ._regex import RegexHighlighter
from ._repl import HighlighterRepl
from .. import _ansi


class BasicHighlighter(RegexHighlighter):
    """
    Class for automatic text highlighting of many formats of numeric values and
    known keywords like ``None``, ``False``, ``True``, ``INFO``, ``WARNING``,
    ``ERROR``, HTTP verbs like ``GET``, ``POST``, ...
    """

    Repl = HighlighterRepl

    _highlights_ = (
        # dlint's DUO138 occurs because of patterns "number_*" it seems, however
        # when these patterns are extracted and tested individually, dlint does
        # not emit a DUO138 anymore so not sure it is the pattern itself or a
        # bug in dlint? Adding a noqa statement for the lack of a better
        # option...
        re.compile(  # noqa: DUO138
            r"""
                (?:
                    \b(?P<none>None)\b|
                    \b(?P<false>False)\b|
                    \b(?P<true>True)\b|
                    \b(?P<info>INFO|NOTICE)\b|
                    \b(?P<ok>OK|GOOD)\b|
                    \b(?P<bad>BAD)\b|
                    \b(?P<debug>DEBUG|TEST|TRACE)\b|
                    \b(?P<warning>WARN(?:ING)?|CAUTION|BEWARE)\b|
                    \b(?P<error>
                        ERROR|CRITICAL|EXCEPTION|
                        Exception|Traceback|\w*Error
                    )\b|
                    \b(?P<httpverb>GET|HEAD|POST|OPTIONS|PUT|PATCH|DELETE)\b|
                    (?P<chrono>
                        (?:\b|[\-\+])
                        [0-9]+
                        (?:\:[0-9]{1,2})+
                        (?:[\.\,][0-9]{1,6})?
                    )\b|
                    \b(?P<uuid>
                        [0-9a-fA-F]{8}\-
                        (?:[0-9a-fA-F]{4}\-){3}
                        [0-9a-fA-F]{12}
                    )\b|
                    \b(?P<eui64>
                        (?:[0-9a-fA-F]{1,2}\:){7}[0-9a-fA-F]{1,2}|
                        (?:[0-9a-fA-F]{1,2}\-){7}[0-9a-fA-F]{1,2}|
                        (?:[0-9a-fA-F]{4}\.){3}[0-9a-fA-F]{4}
                    )\b|
                    \b(?P<eui48>
                        (?:[0-9a-fA-F]{1,2}\:){5}[0-9a-fA-F]{1,2}|
                        (?:[0-9a-fA-F]{1,2}\-){5}[0-9a-fA-F]{1,2}|
                        (?:[0-9a-fA-F]{4}\.){2}[0-9a-fA-F]{4}
                    )\b|
                    \b(?P<ipv4>
                        (?:[0-9]{1,3}\.){1,3}
                        [0-9]{1,3}
                    )\b|
                    \b(?P<ipv6>
                        [0-9a-fA-F]{1,4}
                        (?:\:[0-9a-fA-F]{1,4}){1,7}
                        (?:\:{2}(?:[0-9]+/[0-9]+|/[0-9]+))?
                    )\b|
                    (?<!\\)(?P<byte_repr>
                        (?:\\[xX][0-9a-fA-F]+)|
                        (?:\\[bB][01]+)|
                        (?:\\[oO][0-7]+)
                    )|  # no \b
                    \b(?P<number>
                        (?:  # hex
                            [\-\+]?
                            0[xX]
                            [0-9a-fA-F]+
                            (?:_[0-9a-fA-F]+)*
                        )|
                        (?:  # bin
                            [\-\+]?
                            0[bB]
                            [01]+
                            (?:_[01]+)*
                        )|
                        (?:  # oct
                            [\-\+]?
                            0[oO]
                            [0-7]+
                            (?:_[0-7]+)*
                        )|
                        (?<![\-\+a-zA-Z0-9])
                        (?:  # dec, float
                            [\-\+]?
                            [0-9]+
                            (?:
                                (?:_[0-9]+)+  # allow python separator
                                |
                                (?:[\.\,][0-9]+)?
                                (?:[eE][\-\+][0-9]+)?
                            )?
                        )
                    )  # no \b
                )
            """,
            re.ASCII | re.VERBOSE),
    )

    _highlights_repl_ = {
        None: Repl(_ansi.FG8_39, 0),  # fallback; DEEP_SKY_BLUE_1
        "none": Repl(_ansi.FG8_208, 0),  # DARK_ORANGE
        "false": Repl(_ansi.FG8_196, 0),  # RED_1
        "true": Repl(_ansi.FG8_40, 0),  # GREEN_3B
        "ok": Repl(_ansi.FG8_40, 0),  # GREEN_3B
        "bad": Repl(_ansi.FG8_196, 0),  # RED_1
        "debug": Repl(_ansi.FG8_165, 0),  # MAGENTA_2A
        "warning": Repl(_ansi.FG8_208, 0),  # DARK_ORANGE
        "error": Repl(_ansi.FG8_196, 0),  # RED_1
        "byte_repr": Repl(_ansi.FG8_51, 0),  # CYAN_1
        "number": Repl(_ansi.FG8_51, 0),  # CYAN_1
    }

    _assert_unoptimized_regex_ = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ExtendedHighlighter(BasicHighlighter):
    """Same as `BasicHighlighter` with URIs matching"""

    Repl = HighlighterRepl

    _highlights_ = (
        re.compile(
            r"""
                (?:
                    (?P<uri>
                        [a-zA-Z][a-zA-Z0-9\-\+\.]*
                        ://
                        [-0-9a-zA-Z$_+!`(),.?/;:&=%#]*
                    )|
                    (?P<logmark_debug>\[[dD]\])|
                    (?P<logmark_info>\[[iI]\])|
                    (?P<logmark_notice>\[\+\])|
                    (?:
                        (?P<attr_spec>\*+)?
                        (?P<attr_name>[a-zA-Z\_]\w*)
                        (?P<attr_op>\=)
                    )
                )
            """,
            re.ASCII | re.VERBOSE),
        *BasicHighlighter._highlights_
    )

    _highlights_repl_ = {
        # do not use dict union operator here,
        # it appeared in 3.9 and we want to support 3.8
        **BasicHighlighter._highlights_repl_,

        "uri": Repl(_ansi.FG8_243, 0),  # GREY_46
        "logmark_debug": Repl(_ansi.FG8_165, 0),  # MAGENTA_2A
        "logmark_info": Repl(_ansi.FG8_243, 0),  # GREY_46
        "logmark_notice": Repl(_ansi.FG8_10, 0),  # LIGHT_GREEN
        "attr_spec": Repl(_ansi.FG8_202, 0),  # ORANGE_RED_1
        "attr_name": Repl(_ansi.FG8_208, 0),  # DARK_ORANGE
        "attr_op": Repl(_ansi.FG8_202, 0),  # ORANGE_RED_1
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


#: Alias for `ExtendedHighlighter`
DefaultHighlighter = ExtendedHighlighter
