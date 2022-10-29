# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import sys
import unittest

import coloration


class TestCaseBase(unittest.TestCase):
    def setUp(self):
        coloration.enable_windows_vt100(raise_errors=True)

    def tearDown(self):
        # try to emit a RESET sequence in case something went wrong
        for stream in (sys.stderr, sys.stderr):
            try:
                stream.reset_style()  # ColorationStream method
            except AttributeError:
                if stream.isatty():
                    stream.write(coloration.RESET_STR)
