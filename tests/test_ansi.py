# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import unittest

import coloration

from ._common import TestCaseBase


class TestAnsi(TestCaseBase):
    def test_ansi_color(self):
        for hexcolor in (("#040506", ), (b"#040506", ), (4, 5, 6)):
            fore = coloration.ansi_color(*hexcolor)
            self.assertIsInstance(fore, coloration.AnsiForeRgb)
            self.assertIsInstance(fore, coloration.AnsiForeColorType)
            self.assertIsInstance(fore, coloration.AnsiRgbColorType)
            self.assertIsInstance(fore, coloration.AnsiColorType)
            self.assertIsInstance(fore, coloration.AnsiSGRType)
            self.assertIsInstance(fore, coloration.AnsiDynCode)
            self.assertEqual(fore.str_value, "38;2;4;5;6")
            self.assertEqual(fore.bin_value, b"38;2;4;5;6")
            self.assertEqual(fore.str_sequence, "\033[38;2;4;5;6m")
            self.assertEqual(fore.bin_sequence, b"\033[38;2;4;5;6m")

        back = fore.to_back()
        self.assertIsInstance(back, coloration.AnsiBackRgb)
        self.assertIsInstance(back, coloration.AnsiBackColorType)
        self.assertIsInstance(back, coloration.AnsiRgbColorType)
        self.assertIsInstance(back, coloration.AnsiColorType)
        self.assertIsInstance(back, coloration.AnsiSGRType)
        self.assertIsInstance(back, coloration.AnsiDynCode)
        self.assertEqual(back.str_value, "48;2;4;5;6")
        self.assertEqual(back.bin_value, b"48;2;4;5;6")
        self.assertEqual(back.str_sequence, "\033[48;2;4;5;6m")
        self.assertEqual(back.bin_sequence, b"\033[48;2;4;5;6m")

    def test_ansi_decode(self):
        self.assertEqual("", coloration.ansi_decode(b""))
        self.assertEqual("Hello World!", coloration.ansi_decode(b"Hello World!"))
        with self.assertRaises(ValueError):
            coloration.ansi_decode(123)

    def test_ansi_encode(self):
        self.assertEqual(b"", coloration.ansi_encode(""))
        self.assertEqual(b"Hello World!", coloration.ansi_encode("Hello World!"))
        with self.assertRaises(ValueError):
            coloration.ansi_encode(123)

    def test_ansi_join(self):
        data = coloration.ansi_join(
            coloration.AnsiForeRgb(255, 0, 0),
            "hello ",
            coloration.AnsiForeRgb(255, 255, 0),
            coloration.AnsiBackRgb(0, 0, 255),
            "world",
            coloration.AnsiForeRgb(255, 0, 255),
            "!")

        self.assertEqual(data, (
            "\x1b[38;2;255;0;0mhello "
            "\x1b[38;2;255;255;0;48;2;0;0;255mworld"
            "\x1b[38;2;255;0;255m!"))

    def test_ansi_strip(self):
        data = (
            "\x1b[38;2;255;0;0mhello "
            "\x1b[38;2;255;255;0;48;2;0;0;255mworld"
            "\x1b[38;2;255;0;255m!")
        data = coloration.ansi_strip(data)
        self.assertEqual(data, "hello world!")

        data = "\x1b]0;Some Title!\x07"
        data = coloration.ansi_strip(data)
        self.assertEqual(data, "")

        data = "Foo\x1b]0;Some Title!\x07Bar"
        data = coloration.ansi_strip(data)
        self.assertEqual(data, "FooBar")

    def test_ansi_title(self):
        data = coloration.ansi_title("Some Title!")
        self.assertEqual(data, "\x1b]0;Some Title!\x07")


if __name__ == "__main__":
    unittest.main()
