# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import unittest

import coloration

from ._common import TestCaseBase


class TestHighlighting(TestCaseBase):
    def test_highlighting(self):
        TESTS = (
            'GET http://127.0.0.1',
            '\x1b[38;5;39mGET\x1b[39m \x1b[38;5;243mhttp://127.0.0.1\x1b[39m',

            'foo=123',
            '\x1b[38;5;208mfoo\x1b[39m\x1b[38;5;202m=\x1b[39m\x1b[38;5;51m123\x1b[39m',

            '*_hello123="world"',
            '\x1b[38;5;202m*\x1b[39m\x1b[38;5;208m_hello123\x1b[39m\x1b[38;5;202m=\x1b[39m"world"',  # noqa: E501

            '6.5s elapsed',
            '\x1b[38;5;51m6.5\x1b[39ms elapsed',

            '0xb4, 0xC0B4, \\xA2, \\o755...',
            '\x1b[38;5;51m0xb4\x1b[39m, \x1b[38;5;51m0xC0B4\x1b[39m, \x1b[38;5;51m\\xA2\x1b[39m, \x1b[38;5;51m\\o755\x1b[39m...',  # noqa: E501

            '1234, 1_234, 0x1_234...',
            '\x1b[38;5;51m1234\x1b[39m, \x1b[38;5;51m1_234\x1b[39m, \x1b[38;5;51m0x1_234\x1b[39m...',  # noqa: E501

            'FooBarError exception',
            '\x1b[38;5;196mFooBarError\x1b[39m exception',

            '8cd7275a-8980-4b0c-9f51-88b5392a01a1 UUID',
            '\x1b[38;5;39m8cd7275a-8980-4b0c-9f51-88b5392a01a1\x1b[39m UUID',

            '{8cd7275a-8980-4b0c-9f51-88b5392a01a1} UUID',
            '{\x1b[38;5;39m8cd7275a-8980-4b0c-9f51-88b5392a01a1\x1b[39m} UUID',

            '0:01:53.12345 elapsed',
            '\x1b[38;5;39m0:01:53.12345\x1b[39m elapsed',

            '+0:01:53.12345 elapsed',
            '\x1b[38;5;39m+0:01:53.12345\x1b[39m elapsed',

            '-0:01:53 elapsed',
            '\x1b[38;5;39m-0:01:53\x1b[39m elapsed',

            'ab:cd:ef:01:23:45 eui48',
            '\x1b[38;5;39mab:cd:ef:01:23:45\x1b[39m eui48',

            'ab:cd:ef:01:23:45:00 nothing known',
            '\x1b[38;5;39mab:cd:ef:01:23:45\x1b[39m:\x1b[38;5;51m00\x1b[39m nothing known',  # noqa: E501

            'ab:cd:ef:01:23:45:67:89 eui64',
            '\x1b[38;5;39mab:cd:ef:01:23:45:67:89\x1b[39m eui64',
        )

        hl = coloration.select_highlighter()
        tests_it = iter(TESTS)
        while True:
            try:
                orig = next(tests_it)
            except StopIteration:
                break

            expected = next(tests_it)

            # print(repr(orig) + ",")
            # print(repr(hl(orig)) + ",")
            # print()

            self.assertEqual(hl(orig), expected)


if __name__ == "__main__":
    unittest.main()
