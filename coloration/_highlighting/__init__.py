# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

from ._highlighter import Highlighter

from ._span import HighlighterSpan, HighlighterRegion

from ._repl import (
    HighlighterRepl,
    HighlighterPreparedRepl,
    HighlighterPreparedReplBin,
    HighlighterPreparedReplStr)

from ._regex import RegexHighlighter

from ._default import BasicHighlighter, DefaultHighlighter, ExtendedHighlighter

from ._utils import highlight, select_highlighter
