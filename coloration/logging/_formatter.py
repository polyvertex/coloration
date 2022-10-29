# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import re

from . import _logging


class ColorationLogFormatter(_logging.Formatter):
    """
    A wrapper around `logging.Formatter` whose only feature is to support extra
    placeholder ``%l`` (letter ``L``) to have milliseconds added to *datefmt*.

    It is the equivalent of having ``%(msecs)03d`` in *fmt*, except that
    milliseconds are now part of ``%(asctime)s``, which is more convenient for
    per-field styling.
    """

    MSECS_REGEX = re.compile(r"(?<!%)%l", re.A)

    def __init__(self, /, **kwargs):
        super().__init__(**kwargs)

        # modify formatter's defaults
        # self.default_time_format = "%Y-%m-%d %H:%M:%S"
        # self.default_msec_format = "%s.%03d"

    def formatTime(self, record, datefmt=None, **kwargs):
        if datefmt:
            datefmt = self.MSECS_REGEX.sub(f"{int(record.msecs):03}", datefmt)
        return super().formatTime(record, datefmt=datefmt, **kwargs)
