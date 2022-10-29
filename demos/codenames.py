#!/usr/bin/env python

import sys

import _bootstrap  # noqa: F401

import coloration as color


def header(title):
    return color.ansi_join(
        color.STD_BG_DEFAULT, color.WHITE, f"[ {title} ]",
        color.RESET, "\n")


def print_ansi_codes_enums(file=sys.stdout):
    BOX_WIDTH = 5

    file.write(header("STYLE"))
    for style in color.AnsiStyle.__members__.values():
        style_name = color.ansi_code_to_global_name(style)
        style_name = style_name.ljust(10)

        sample_text = "Hello World!"
        sample_text = color.ansi_join(style, sample_text, color.RESET)

        file.write(f"{style_name} {sample_text}\n")

    file.write("\n")
    file.write(header("4-BIT STANDARD COLORS"))
    for fore, back in zip(
            color.AnsiStdFore.__members__.values(),
            color.AnsiStdBack.__members__.values()):
        color_box = color.ansi_join(" ", back, " " * BOX_WIDTH, color.RESET)

        fore_name = color.ansi_code_to_global_name(fore)
        fore_name = fore_name.ljust(16)

        back_name = color.ansi_code_to_global_name(back)
        back_name = back_name.ljust(16)

        file.write(f"{color_box} {fore_name} {back_name}\n")

    file.write("\n")
    file.write(header("8-BIT COLORS"))
    for idx, fore, back in zip(
            range(256),
            color.AnsiFore8.__members__.values(),
            color.AnsiBack8.__members__.values()):
        color_box = color.ansi_join(" ", back, " " * BOX_WIDTH, color.RESET)

        color_index = str(idx).ljust(3)

        fore_name = color.ansi_code_to_global_name(fore)
        fore_name = fore_name.ljust(19)

        back_name = color.ansi_code_to_global_name(back)
        back_name = back_name.ljust(19)

        line = f"{color_box} {color_index} {fore_name} {back_name}\n"
        file.write(line)
    assert idx == 255


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

    print_ansi_codes_enums()


if __name__ == "__main__":
    main()
