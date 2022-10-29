#!/usr/bin/env python

import sys

import _bootstrap  # noqa: F401

import coloration


# * Wrap std streams and enable VT100 emulation if on Windows, and if needed
# * This step is not compulsory to use coloration features, but it may improve
#   performances if you do use coloration features a lot in your project
# * NOTE: by default, this does not mean coloring will always be enabled! See
#   below for more info
coloration.init()

# * stdout and stderr are now ColorationStream file-like wrappers
# * However, keep in mind that by default, it does not mean you will always have
#   colored output
# * This is because - by default - ColorationStream:
#   * does not emit ANSI escape sequences on non-TTY files
#   * honors the NO_COLOR environment variable if specified
# * To force coloring on standard streams, call init() as follows:
#     coloration.init(escape=True, styling=True)
# * escape and styling are passed to ColorationStream.__init__()
assert isinstance(sys.stdout, coloration.ColorationStream)
assert isinstance(sys.stderr, coloration.ColorationStream)


# * Highlighters do not require std stream to be wrapped
# * They just take some text as input, and output a modified copy of it
hl = coloration.DefaultHighlighter()

# prepare some text
text = """
    Some keywords like False, True, None, DEBUG, INFO, NOTICE, WARNING, ERROR
    and OK are automatically highlighted with default highlighter, as well as
    UUIDs like 51605be1-b026-4bfe-8934-478092d04376, numbers like 123.4, IPv4
    addresses like 192.168.0.1 (IPv6 addresses supported), HTTP verbs like GET
    and POST, log marks like [i] and [+], and Python-like keyword-value pairs
    like some_var=True.
""".rstrip()

# have it automatically highlighted
text = hl(text)

# print!
print(text)
