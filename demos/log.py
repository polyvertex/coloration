#!/usr/bin/env python

import sys

import _bootstrap  # noqa: F401

import coloration as color
import coloration.logging as logging


# * Wrap std streams and enable VT100 emulation if on Windows, and if needed
# * This step is not compulsory to use coloration features, but it may improve
#   performances if you do use coloration features a lot in your project
# * NOTE: by default, this does not mean coloring will always be enabled! See
#   below for more info
color.init()

# * stdout and stderr are now ColorationStream file-like wrappers
# * However, keep in mind that by default, it does not mean you will always have
#   colored output
# * This is because - by default - ColorationStream:
#   * does not emit ANSI escape sequences on non-TTY files
#   * honors the NO_COLOR environment variable if specified
# * To force coloring on standard streams, call init() as follows:
#     coloration.init(escape=True, styling=True)
# * escape and styling are passed to ColorationStream.__init__()
assert isinstance(sys.stdout, color.ColorationStream)
assert isinstance(sys.stderr, color.ColorationStream)


# * coloration provides a logging Handler derived from logging.StreamHandler
# * By default, ColorationStreamHandler writes on std.stderr, like standard
#   logging.StreamHandler would do...
# * ... and it enables coloring and a default regex-based message highlighting
#   as long as the output stream is connected to a TTY, and NO_COLOR environment
#   variable is NOT declared

# coloration's logging subpackage aims to provides API compatibility with
# standard logging package for its base features, such that you can use it as a
# drop-in replacement in most use cases
logging.basicConfig(handlers=[logging.ColorationStreamHandler()])

# Get root logger, as you would do with standard logging package
logger = logging.getLogger()

# Lower logger's log level to DEBUG, such that all the messages emitted below
# get actually displayed for the purpose of this demo (default level is WARNING)
logger.setLevel(logging.DEBUG)

logger.debug("Debug messages are suffixed with source info")
logger.info("Some informational message")
logger.notice("A NOTICE has a slightly higher priority than an INFO message")
logger.warning("This is some test WARNING  <- auto highlighted keyword")
logger.error("And an ERROR message")

try:
    raise RuntimeError("oops! this is a test")
except RuntimeError:
    logger.exception("Dummy exception log message")

logger.info("This demo took 0.1 second to run")
