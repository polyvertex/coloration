#!/usr/bin/env python

import sys

import _bootstrap  # noqa: F401

import coloration as color


def header(title):
    return color.ansi_join(
        color.STD_BG_DEFAULT, color.WHITE, f"[ {title} ]",
        color.RESET, "\n")


def color8_box(color_index, *, width=5):
    assert isinstance(color_index, int)
    assert 0 <= color_index <= 255

    back = getattr(color, f"BG8_{color_index}")

    # foreground color (black or white)
    if color_index < 8:
        fore = color.WHITE
    elif color_index < 16 or color_index >= 244:
        fore = color.BLACK
    elif color_index >= 232:
        fore = color.WHITE
    else:
        normalized = (color_index - 16) % 36 + 16
        if normalized >= 16 and normalized <= 33:
            fore = color.WHITE
        else:
            fore = color.BLACK

    label = str(color_index).center(width, " ")

    return color.ansi_join(fore, back, label, color.RESET)


def print_8bit_colors_palette(file=sys.stdout):
    """Print standard 8-bit colors palette on *file*"""
    # standard colors
    file.write(header("8-BIT STANDARD COLORS"))
    for color_index in range(0, 8):
        file.write(color8_box(color_index))
    file.write("\n")
    for color_index in range(8, 16):
        file.write(color8_box(color_index))
    file.write("\n")

    # 216 colors
    file.write("\n")
    file.write(header("8-BIT 216 COLORS"))
    for group in range(2):
        if group:
            file.write("\n")

        for color_index in range(16, 232):
            tmp = (color_index - 16) % 36 + 16
            if not ((group == 0 and tmp <= 33) or (group == 1 and tmp > 33)):
                continue

            if tmp in (22, 28, 40, 46):
                file.write("  ")

            file.write(color8_box(color_index))

            if tmp in (33, 51):
                file.write("\n")

    # grayscale colors
    file.write("\n")
    file.write(header("8-BIT GRAYSCALE COLORS"))
    for color_index in range(232, 244):
        file.write(color8_box(color_index))
    file.write("\n")
    for color_index in range(244, 256):
        file.write(color8_box(color_index))
    file.write("\n")


def main():
    # * Wrap std streams and enable VT100 emulation if on Windows, and if needed
    # * This step is not compulsory to use coloration features, but it may
    #   improve performances if you do use coloration features a lot in your
    #   project
    # * NOTE: by default, this does not mean coloring will always be enabled!
    #   See below for more info
    color.init()

    # * stdout and stderr are now ColorationStream file-like wrappers
    # * However, keep in mind that by default, it does not mean you will always
    #   have colored output
    # * This is because - by default - ColorationStream:
    #   * does not emit ANSI escape sequences on non-TTY files
    #   * honors the NO_COLOR environment variable if specified
    # * To force coloring on standard streams, call init() as follows:
    #     coloration.init(escape=True, styling=True)
    # * escape and styling are passed to ColorationStream.__init__()
    assert isinstance(sys.stdout, color.ColorationStream)
    assert isinstance(sys.stderr, color.ColorationStream)

    print_8bit_colors_palette()


if __name__ == "__main__":
    main()
