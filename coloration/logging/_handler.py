# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import os
import sys

from . import _logging
from ._formatter import ColorationLogFormatter
from .. import _ansi
from .._ansi import ansi_join
from .._highlighting import select_highlighter
from .._stream import ColorationStream
from .._utils import is_file_tty


class ColorationStreamHandler(_logging.StreamHandler):
    """A wrapper around `logging.StreamHandler` to have colored log lines"""

    #: Default *datefmt* value for a TTY stream
    DATEFMT_TTY = "%H:%M:%S.%l"

    #: Default *datefmt* value for a non-TTY stream
    DATEFMT_NONTTY = "%Y-%m-%d %H:%M:%S.%l"

    #: Styling for the date field (only if *datefmt* was specified or `True` or
    #: `None`).
    #:
    #: Set to `None` to disable this feature.
    DATE_STYLE = _ansi.FG8_60  # MEDIUM_PURPLE_4

    #: ``record.levelname`` translation map for a TTY stream
    #:
    #: * This dict can be empty
    #: * Not translation of ``record.levelname`` occurs if a level is not found
    LEVELNAME_MAP_TTY = {
        _logging.DEBUG: "[D]",
        _logging.INFO: "[i]",
        _logging.NOTICE: "[+]"}

    #: Same as `LEVELNAME_MAP_TTY` for a non-TTY stream
    #:
    #: * This dict can be empty
    #: * Not translation of ``record.levelname`` occurs if a level is not found
    LEVELNAME_MAP_NONTTY = {}

    #: Styling of the level name to be inserted by this handler (only if
    #: *styling* is enabled)
    #:
    #: * No styling is applied unless *styling* is enabled and level is found in
    #:   this dict.
    #: * Make this dict empty to fully disable this feature.
    LEVELNAME_STYLE_MAP = {
        _logging.DEBUG: _ansi.FG8_165,  # MAGENTA_2A
        _logging.INFO: _ansi.FG8_243,  # GREY_46
        _logging.NOTICE: _ansi.FG8_10,  # LIGHT_GREEN
        _logging.WARNING: _ansi.FG8_208,  # DARK_ORANGE
        _logging.ERROR: _ansi.FG8_196,  # RED_1
        _logging.CRITICAL: _ansi.FG8_196}  # RED_1

    #: Default log level above which this handler will not append source info,
    #: for a TTY stream
    #:
    #: * You can override this value with argument *srcinfo*
    #: * Set *srcinfo* argument to ``-1`` to disable this feature.
    SOURCEINFO_MAXLEVEL_TTY = _logging.DEBUG

    #: Same as `SOURCEINFO_MAXLEVEL_TTY` for a non-TTY stream
    #:
    #: Default is an arbitrary big value, such that source info is always
    #: inserted.
    SOURCEINFO_MAXLEVEL_NONTTY = 1_000_000

    #: Default styling for the *source* field
    #:
    #: Set to `None` to disable this feature.
    SOURCEINFO_STYLE = _ansi.FG8_60  # MEDIUM_PURPLE_4

    #: Default *fmt* value to pass to the `logging.Formatter`, for a TTY stream
    #:
    #: Use with care as you may obtain undesired results since this handler does
    #: insert extra data to the final log line, depending on the arguments
    #: passed to the its constructor.
    DEFAULT_FORMAT_TTY = {
        "%": "%(message)s",
        "{": "{message}",
        "$": "${message}"}

    #: Same as `DEFAULT_FORMAT_TTY` for a non-TTY stream
    DEFAULT_FORMAT_NONTTY = {
        "%": "[%(process)d] %(levelname)s %(message)s",
        "{": "[{process}] {levelname} {message}",
        "$": "[${process}] ${levelname} ${message}"}

    def __init__(
            self, *, stream=None, styling=None, datefmt=None, levelinfo=None,
            highlighter=None, srcinfo=None, fmt_args=None):
        #
        # stream
        #

        # defaults to stderr (same as logging.StreamHandler)
        if stream is None:
            stream = sys.stderr

        # we must create our own ColorationStream instance because this one may
        # have highlighting enabled, which would collide with the formatting
        # applied by this Handler
        if isinstance(stream, ColorationStream):
            # honor stream's config in case caller does not want to force styling
            if styling is None:
                styling = stream.can_style

            stream = stream.wrapped

        is_tty = is_file_tty(stream)

        if styling is None:
            styling = is_tty and "NO_COLOR" not in os.environ
        else:
            styling = bool(styling)

        stream = ColorationStream(
            stream, acquire=False, escape=styling, highlighter=False,
            autoreset=False, autostrip=False)

        # standard logging package does not support binary streams
        if stream.is_binary:
            raise ValueError("binary stream not supported")

        super().__init__(stream=stream)

        #
        # custom features
        #

        # datefmt
        if datefmt is False:
            datefmt = None  # this handler will not insert date
        elif datefmt is None or datefmt is True:
            datefmt = self.DATEFMT_TTY if is_tty else self.DATEFMT_NONTTY
        elif not datefmt or not isinstance(datefmt, str):
            raise ValueError("datefmt")

        # fmt_args
        fmt_args = fmt_args.copy() if fmt_args else {}
        fmt_args.setdefault("style", "%")
        fmt_args["datefmt"] = datefmt  # yes, overwrite
        fmt_args.setdefault(
            "fmt", (
                self.DEFAULT_FORMAT_TTY[fmt_args["style"]] if is_tty
                else self.DEFAULT_FORMAT_NONTTY[fmt_args["style"]]))

        # levelinfo
        if levelinfo is None:
            levelinfo = (
                is_tty or
                "fmt" not in fmt_args or
                "levelname" not in fmt_args["fmt"])
        elif levelinfo is False or levelinfo is True:
            pass
        else:
            raise ValueError("levelinfo")

        # srcinfo
        # convert to a record.levelno compatible value
        if srcinfo is None:
            srcinfo = (
                self.SOURCEINFO_MAXLEVEL_TTY if is_tty
                else self.SOURCEINFO_MAXLEVEL_NONTTY)
        elif srcinfo is False:
            # an arbitrary very low value, such that this handler never inserts
            # srcinfo
            srcinfo = -1_000_000
        elif srcinfo is True:
            # an arbitrary very high value, such that this handler always
            # inserts srcinfo
            srcinfo = 1_000_000
        elif not isinstance(srcinfo, int):
            raise ValueError("srcinfo")

        # assign a formatter so that:
        # * logging.basicConfig() does not try to assign its default one
        # * we can add support for an extra placeholder "%l" (msecs) in datefmt
        formatter = ColorationLogFormatter(**fmt_args)
        super().setFormatter(formatter)

        # ensure that super().setFormatter() is still implemented as expected
        # Handler.formatter is the attribute checked by logging.basicConfig() to
        # know whether it should setFormatter() by itself, so we must ensure it
        # is set already
        assert self.formatter is formatter

        self._can_style = styling
        self._insert_date = bool(datefmt)
        self._insert_level = levelinfo
        self._srcinfo_maxlevel = srcinfo
        self._levelname_map = (
            self.LEVELNAME_MAP_TTY if is_tty else self.LEVELNAME_MAP_NONTTY)

        if not styling:
            self._date_style = None
            self._levelname_style_map = {}
            self._highlighter = None
            self._sourceinfo_style = None
        else:
            self._date_style = self.join_styles(self.DATE_STYLE)
            self._levelname_style_map = {
                k: self.join_styles(v)
                for k, v in self.LEVELNAME_STYLE_MAP.items()}
            self._highlighter = select_highlighter(
                highlighter, binary=stream.is_binary)
            self._sourceinfo_style = self.join_styles(self.SOURCEINFO_STYLE)

    def setFormatter(self, *args, **kwargs):
        # method inherited from logging.Handler
        raise NotImplementedError("feature disabled by this Handler")

    def setStream(self, *args, **kwargs):
        # method inherited from logging.StreamHandler
        raise NotImplementedError("feature disabled by this Handler")

    def format(self, record, *args, **kwargs):
        def _append(*items):
            if output:
                output.append(sep)
            output.extend(items)

        output = []
        sep = " "
        rst = _ansi.RESET_STR

        # date part
        if self._insert_date:
            part = self.formatter.formatTime(
                record=record,
                datefmt=self.formatter.datefmt)

            if self._date_style:
                _append(self._date_style, part, rst)
            else:
                _append(part)

        # level part
        if self._insert_level:
            part = self._levelname_map.get(record.levelno, record.levelname)

            if not self._levelname_style_map:
                _append(part)
            else:
                try:
                    style = self._levelname_style_map[record.levelno]
                except KeyError:
                    _append(part)
                else:
                    if style:
                        _append(style, part, rst)

        # message part: prepare highlighting if needed
        if self._highlighter is not None:
            # we want to highlight only the already-formatted *message* part so
            # monkey-patch record.getMessage() temporarily in order to get the
            # value before it gets added extra data that we want excluded from
            # highlighting
            def _get_highlighted_message():
                return self._highlighter(orig_getmsg()) + rst

            # make exc_text if required (the same way it is done by default
            # Formatter), so that we can highlight exc_text as well
            if record.exc_info and not record.exc_text:
                record.exc_text = self.formatter.formatException(record.exc_info)

            orig_getmsg = record.getMessage
            orig_exctext = record.exc_text
            orig_stackinfo = record.stack_info

            if orig_exctext:
                record.exc_text = self._highlighter(record.exc_text)

            if orig_stackinfo:
                record.stack_info = self._highlighter(record.stack_info)

            record.getMessage = _get_highlighted_message

        # message part
        try:
            part = super().format(record, *args, **kwargs)
        finally:
            if self._highlighter is None:
                _append(part)
            else:
                record.getMessage = orig_getmsg
                record.exc_text = orig_exctext
                record.stack_info = orig_stackinfo
                del orig_getmsg, orig_exctext, orig_stackinfo
                _append(part, rst)

        # srcinfo part
        if record.levelno <= self._srcinfo_maxlevel:
            part = f"<{record.module}:{record.lineno}>"
            if not self._sourceinfo_style:
                _append(sep, part)
            else:
                _append(sep, self._sourceinfo_style, part, rst)

        return "".join(output)

    @staticmethod
    def join_styles(styles):
        if styles is None:
            return None
        if not isinstance(styles, (tuple, list)):
            styles = (styles, )
        return ansi_join(*styles, binary=False)
