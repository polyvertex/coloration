#!/usr/bin/env python3

import os.path
import sys
import unittest

import setuptools


if len(sys.argv) >= 2 and sys.argv[1] == "test":
    # setuptools' test command is deprecated, this enables backward
    # compatibility while bypassing setuptools entirely
    assert len(sys.argv) == 2, "extra arguments ignored"
    PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
    TESTS_DIR = os.path.join(PROJECT_DIR, "tests")
    unittest.main(
        module=None, argv=[
            "unittest", "discover", "--verbose",
            "--start-directory", TESTS_DIR,
            "--pattern", "test_*.py",
            "--top-level-directory", PROJECT_DIR])
else:
    setuptools.setup()
