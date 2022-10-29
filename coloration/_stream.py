# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import contextlib
import io
import locale
import os
import sys

from ._ansi import _codes_flat
from ._ansi._codes import AnsiCode, AnsiControl, AnsiSGRType
from ._ansi._utils import ansi_autoreset, ansi_join, ansi_strip, ansi_title
from ._highlighting import Highlighter, select_highlighter
from ._utils import is_file_tty, is_file_writable


class ColorationStream:
    """
    A wrapper around any kind of file-object (text and binary streams
    supported), with convenience features to deal with the `ANSI escape codes
    <https://en.wikipedia.org/wiki/ANSI_escape_code>`_ supported by this
    library.

    The *acquire*, *escape*, *styling*, *autoreset* and *autostrip* parameters
    can be assigned either `None` (meaning *automatic detection*, which is the
    default) or a `bool` value to explicitly and forcefully enable or disable
    their respective feature.

    *acquire* indicates whether this wrapper may acquire ownership of the
    *stream*, resulting in auto-closing the stream upon the destruction of this
    instance.

    If *acquire* is `None`, it is enabled by default unless the provided stream
    is any of the so-called standard streams (i.e. ``sys.std*`` or
    ``sys.__std*__``), in which case *acquire* is forcefully disabled regardless
    of its initial value.

    *escape* indicates whether this wrapper is allowed to emit any form of ANSI
    escape sequences.

    *styling* indicates whether this wrapper is allowed to emit specifically
    ANSI SGR sequences (styling and coloring). A `None` value allows to comply
    to both the *escape* argument and the ``NO_COLOR`` environment variable.
    Note that *styling* is forcefully disabled if *escape* is disabled.

    *highlighter* can be strictly `False` (no auto-highlighting), strictly
    `None` (`DefaultHighlighter` is assigned), or a custom highlighter object
    derived from `Highlighter`, or a callable that takes the text to highlight
    as a single parameter and that returns the (highlighted) text.

    *highlighter*, if any, is used only if *styling* is enabled (explicitly or
    not).

    *highlighter* can be changed any time by setting property ``highlighter``.

    *autoreset* (disabled by default) indicates whether this class should
    automatically insert a `AnsiStyle.RESET` sequence after every call to
    ``write(data)``, as long as a ``CSI`` is found in *data*.

    *autostrip* indicates whether ANSI Control Sequences (CSI) and Operating
    System Commands (OSC) should be stripped out from data before it being
    written. This option overrides *escape* and *autoreset*.
    """

    def __init__(
            self, stream, *,
            acquire=None, escape=None, styling=None, highlighter=False,
            autoreset=None, autostrip=None):
        if stream is None:
            is_tty = False
            is_binary = False
            encoding = None
            encoding_errors = None
        else:
            if isinstance(stream, ColorationStream):
                raise ValueError("wrap the wrapper?")

            if not is_file_writable(stream):
                raise ValueError("stream not writable")

            is_tty = is_file_tty(stream)

            is_binary = not isinstance(stream, io.TextIOBase)

            try:
                encoding = stream.encoding
            except AttributeError:
                encoding = None
            else:
                if not encoding or not isinstance(encoding, str):
                    encoding = (
                        None if is_binary
                        else locale.getpreferredencoding(False))

            try:
                encoding_errors = stream.errors
            except AttributeError:
                encoding_errors = None
            else:
                if not encoding_errors or not isinstance(encoding_errors, str):
                    encoding_errors = None

        # sanitize *acquire*
        acquire = True if acquire is None else bool(acquire)
        if acquire:
            # safety check: forcefully disable ownership if *stream* is one of
            # the standard streams
            for stdstream in (
                    sys.stdin, sys.__stdin__,
                    sys.stdout, sys.__stdout__,
                    sys.stderr, sys.__stderr__):
                if stream is stdstream:
                    acquire = False
                    break

        # sanitize *autostrip*
        if autostrip is None:
            # keep that case explicit instead of a bool() cast as done below
            autostrip = False
        else:
            autostrip = bool(autostrip)

        # sanitize *escape*
        if escape is None:
            escape = is_tty and not autostrip
        else:
            escape = bool(escape) and not autostrip

        # sanitize *styling*
        if styling is None:
            styling = escape and "NO_COLOR" not in os.environ
        else:
            styling = bool(styling) and escape and not autostrip

        # sanitize *autoreset*
        if not escape:
            autoreset = False
        elif autoreset is None:
            autoreset = False  # escape and not autostrip
        else:
            autoreset = styling and bool(autoreset) and not autostrip

        #
        # private properties
        #

        self._wrapped = stream
        self._owns_wrapped = acquire
        self._is_tty = is_tty
        self._is_binary = is_binary
        self._encoding = encoding
        self._encoding_errors = encoding_errors
        self._can_escape = escape
        self._can_style = styling
        self._highlighter = select_highlighter(highlighter, binary=is_binary)
        self._can_autoreset = autoreset
        self._can_autostrip = autostrip

        # sanity checks
        if __debug__:
            if self._can_style:
                assert self._can_escape
                # assert not self._can_autoreset

            if self._can_autostrip:
                assert not self._can_escape
                assert not self._can_autoreset

            if self._can_autoreset:
                assert self._can_style
                assert self._can_escape

        # internal utility properties mainly to speed-up writing
        if is_binary:
            self._empty = b""
            self._csi = _codes_flat.CSI.bin_value
            self._semicolon = b";"
            self._m = b"m"
            self._reset = _codes_flat.RESET.bin_sequence
            self._default_sep = b" "
            self._default_end = b"\n"
        else:
            self._empty = ""
            self._csi = _codes_flat.CSI.str_value
            self._semicolon = ";"
            self._m = "m"
            self._reset = _codes_flat.RESET.str_sequence
            self._default_sep = " "
            self._default_end = "\n"

    def __del__(self):
        if self._owns_wrapped:
            self.close()

    def __getattr__(self, name):
        return getattr(self._wrapped, name)

    @property
    def wrapped(self):
        """The wrapped file-object"""
        return self._wrapped

    @property
    def owns_wrapped(self):
        """
        Is the wrapped file-object owned by this wrapper?

        This depends on constructor's *acquire* argument.
        """
        return self._owns_wrapped

    @property
    def is_binary(self):
        """Is the wrapped file-object detected as binary?"""
        return self._is_binary

    @property
    def encoding(self):
        """The detected *encoding* value of the wrapped stream"""
        return self._encoding

    @property
    def encoding_errors(self):
        """The detected *encoding_errors* value of the wrapped stream"""
        return self._encoding_errors

    @property
    def can_escape(self):
        """
        A `bool` value that indicate whether this wrapper is allowed to emit any
        form of ANSI escape sequences.
        """
        return self._can_escape

    @property
    def can_style(self):
        """
        A `bool` value that indicate whether this wrapper is allowed to emit
        ANSI SGR escape sequences (styling and coloring).

        This property can be changed at any time. Forcing it to a true value
        also enables escaping, thus changing the `can_escape` property to true
        as well.
        """
        return self._can_style

    @can_style.setter
    def can_style(self, can_style):
        if not can_style:
            self._can_style = False
        else:
            self._can_style = True
            self._can_escape = True

    @property
    def highlighter(self):
        """
        The `coloration.Highlighter` object associated to this stream. Can be
        `None`.

        The highlighter can be changed at any time, however it is used only if
        `can_style` is true.
        """
        return self._highlighter

    @highlighter.setter
    def highlighter(self, highlighter):
        self._highlighter = select_highlighter(
            highlighter, binary=self._is_binary)

    @property
    def can_autoreset(self):
        """
        A `bool` value that indicate whether this wrapper is allowed to emit an
        `AnsiStyle.RESET` sequence at the end of a data sequence in which at
        least one ANSI SGR sequence has been detected.
        """
        return self._can_autoreset

    @property
    def can_autostrip(self):
        """
        A `bool` value that indicate whether this wrapper will strip all the
        supported ANSI escape sequences detected in the data to write, before
        writing.
        """
        return self._can_autostrip

    @property
    def closed(self):
        """
        A `bool` value that indicate whether this file is closed (or this
        wrapper detached)
        """
        wrapped = self._wrapped

        if wrapped is None:
            return True

        try:
            closed = wrapped.closed
        except AttributeError:
            # assume wrapped file is still open
            return False
        else:
            # standard attribute is not a callable
            if not callable(closed):
                return bool(closed)
            return bool(closed())

    def close(self):
        """
        Close the wrapped stream, regardless of ownership status (i.e.
        constructor's *acquire* argument)

        .. seealso:: `detach()`
        """
        wrapped = self._wrapped
        if wrapped is not None:
            self._wrapped = None

            if self._can_style:
                wrapped.write(self._reset)
                with contextlib.suppress(AttributeError, TypeError):
                    wrapped.flush()

            try:
                close_method = wrapped.close
            except AttributeError:
                pass
            else:
                if callable(close_method):
                    close_method()
            finally:
                close_method = None

            wrapped = None

    def detach(self):
        """
        Detach the wrapped stream and return it.

        This method **does not** close the wrapped stream.

        Return `None` if `detach()` or `close()` was already called, or if no
        stream were ever attached to this wrapper.

        .. seealso:: `close()`
        """
        wrapped = self._wrapped
        self._wrapped = None
        return wrapped

    def isatty(self):
        """
        Return a `bool` that indicates whether wrapped stream is a TTY.

        PyCharm supported.
        """
        wrapped = self._wrapped
        if wrapped is None:
            raise RuntimeError("stream closed")
        return self._is_tty

    def flush(self):
        """
        Wrapped stream's ``flush()`` method, if any.

        This method does not fail if wrapped stream does not have a ``flush``
        callable attribute.
        """
        # flush() may be called pretty often so explicitly wrap it to avoid
        # having to resolve it via __getattr__() every time
        wrapped = self._wrapped
        if wrapped is None:
            raise RuntimeError("stream closed")

        try:
            return wrapped.flush()
        except (AttributeError, TypeError):
            return None

    def write(self, data):
        """
        Wrapped stream's ``write()`` method.

        This method returns `None` since it may change *data* and its length,
        which would make the value returned by the underlying ``write()``
        meaningless to the caller.
        """
        wrapped = self._wrapped
        if wrapped is None:
            raise RuntimeError("stream closed")

        if self._can_autostrip:
            data = ansi_strip(data)
        else:
            if self._can_style and self._highlighter is not None:
                data = self._highlighter(data)

            if self._can_autoreset:
                data = ansi_autoreset(data)

        wrapped.write(data)
        # return None, see docstring

    def set_title(self, title):
        """
        Emit an OSC sequence using *title* in order to change terminal's title.

        *title* is assumed to be of the appropriate type already.

        This method honors constructor's *escape* and *autostrip* arguments.

        This method implicitly flushes stream.
        """
        wrapped = self._wrapped
        if wrapped is not None and self._can_escape:
            wrapped.write(ansi_title(title))
            with contextlib.suppress(AttributeError, TypeError):
                wrapped.flush()

    def alt_screen(self, enable):
        """Enable or disable alternative screen buffer"""
        if self._can_escape:
            if enable:
                self.control(
                    AnsiControl.ENABLE_ALT_SCREEN,
                    AnsiControl.MOVE_TO_TOPLEFT)
            else:
                self.control(AnsiControl.DISABLE_ALT_SCREEN)

    def reset_style(self):
        """
        Emit an `AnsiStyle.RESET` control code in order to reset every currently
        applied SGR attribute (coloring, styling like italic for instance).

        This method honors constructor's *escape*, *styling* and *autostrip*
        arguments.

        This method implicitly flushes stream.
        """
        wrapped = self._wrapped
        if wrapped is not None and self._can_style:
            # direct call to wrapped's write() so to avoid triggering the ANSI
            # CSI detection feature implemented in self.write()
            wrapped.write(self._reset)
            with contextlib.suppress(AttributeError, TypeError):
                wrapped.flush()

    def control(self, *ansi_codes):
        """
        Emit `AnsiCode` derived objects, like `AnsiControl.CLEAR_SCREEN` or
        `AnsiStyle.ITALIC` for instance, after having joined them with
        `ansi_join()`.

        This method works pretty much like `ColorationStream.print()` in the
        sense it joins (and merges in some cases) the provided data before
        writing it, except it is faster since it does not offer the extra
        features of ``print()``.

        This method honors constructor's *escape*, *styling* and *autostrip*
        arguments.

        This method implicitly flushes stream if it wrote something.
        """
        wrapped = self._wrapped
        if ansi_codes and wrapped is not None and self._can_escape:
            # strip out ANSI SGR codes if styling is not allowed
            if not self._can_style:
                ansi_codes = [
                    code for code in ansi_codes
                    if not isinstance(code, AnsiSGRType)]
                if not ansi_codes:
                    return

            # caller should use sprint() to print arbitrary objects
            autostr = False

            data = ansi_join(
                *ansi_codes, binary=self._is_binary, autostr=autostr,
                encoding=self._encoding, errors=self._encoding_errors)

            wrapped.write(data)

            with contextlib.suppress(AttributeError, TypeError):
                wrapped.flush()

    def cursor_up(self, lines=1):
        """Move cursor up, if escaping is enabled"""
        self.control(AnsiControl.cursor_up(lines))

    def cursor_down(self, lines=1):
        """Move cursor down, if escaping is enabled"""
        self.control(AnsiControl.cursor_down(lines))

    def cursor_forward(self, columns=1):
        """Move cursor forward, if escaping is enabled"""
        self.control(AnsiControl.cursor_forward(columns))

    def cursor_backward(self, columns=1):
        """Move cursor backward, if escaping is enabled"""
        self.control(AnsiControl.cursor_backward(columns))

    def move_to_x(self, x=0):
        """Move cursor to column *x*, if escaping is enabled"""
        self.control(AnsiControl.move_to_x(x))

    def move_to_xy(self, x=0, y=0):
        """Move cursor to column *x* and row *y*, if escaping is enabled"""
        self.control(AnsiControl.move_to_xy(x, y))

    def print(self, *args, flush=False, **kwargs):
        """
        Like standard `.print()` function, but with proper encoding of
        `AnsiCode` values while honoring constructor's options regarding
        styling, stripping, highlighting, ...

        Equivalent of chaining calls to `sprint()`, `write()`, then `flush()`
        (depending on *flush* boolean).

        Argument *flush* is the same than for `.print()`.

        See `sprint()` for more information about the other positional and named
        arguments.
        """
        wrapped = self._wrapped
        if wrapped is None:
            raise RuntimeError("stream closed")

        data = self.sprint(*args, **kwargs)

        if data:
            wrapped.write(data)
            if flush:
                with contextlib.suppress(AttributeError, TypeError):
                    wrapped.flush()

    def sprint(self, *objs, sep=None, end=None, hl=None, autoreset=True):  # noqa: C901
        """
        Like standard `.print()` function, but with proper encoding of
        `AnsiCode` values while honoring constructor's options regarding
        styling, stripping, highlighting, ...

        Returns the result instead of writing it.

        Arguments *objs*, *sep*, and *end* are the same than for `.print()`.

        *hl* (for *highlight*) is an override of constructor's *highlighter*
        argument and it can be `None` (to keep current stream's setup), a
        boolean value, to force enable or disable of highlighting, or a
        `Highlighter` object to both enable the feature and use a particular
        highlighter during this call.

        *autoreset* is enabled by default for this method and is an override of
        constructor's argument. Set to `None` if you prefer to rely on stream's
        configuration, or to `False` to forcefully disable autoreset feature.

        Note that both *hl* and *autoreset* options, if enabled, are applied
        only if escaping is allowed (see constructor's arguments).
        """
        def _flush_sgr():
            nonlocal accumulated_sgr
            if accumulated_sgr:
                if self._can_style:
                    yield self._csi
                    yield self._semicolon.join(accumulated_sgr)
                    yield self._m
                accumulated_sgr.clear()

        def _flush_sep():
            nonlocal must_emit_sep
            if must_emit_sep:
                yield sep
                must_emit_sep = False

        def _iter():
            nonlocal accumulated_sgr
            nonlocal must_emit_sep

            for item in objs:
                if isinstance(item, AnsiSGRType):
                    if self._can_style:
                        if self._is_binary:
                            accumulated_sgr.append(item.bin_value)
                        else:
                            accumulated_sgr.append(item.str_value)
                    elif accumulated_sgr:
                        accumulated_sgr.clear()
                elif isinstance(item, AnsiCode):
                    if self._can_escape:
                        yield from _flush_sgr()
                        if self._is_binary:
                            yield item.bin_sequence
                        else:
                            yield item.str_sequence
                elif isinstance(item, str):
                    if self._is_binary:
                        item = item.encode(self._encoding, self._encoding_errors)
                    yield from _flush_sep()
                    yield from _flush_sgr()
                    yield item
                    must_emit_sep = True
                # elif isinstance(item, (bytes, bytearray)):
                #     if not self._is_binary:
                #         item = item.decode(self._encoding, self._encoding_errors)
                #     yield from _flush_sep()
                #     yield from _flush_sgr()
                #     yield item
                #     must_emit_sep = True
                else:
                    item = str(item)
                    if self._is_binary:
                        item = item.encode(self._encoding, self._encoding_errors)
                    yield from _flush_sep()
                    yield from _flush_sgr()
                    yield item
                    must_emit_sep = True

            if accumulated_sgr:
                yield from _flush_sgr()

        accumulated_sgr = []  # accumulator for SGR sequences
        must_emit_sep = False

        if sep is None:
            sep = self._default_sep
        elif sep is False:
            sep = self._empty

        if end is None:
            end = self._default_end

        data = list(_iter())
        if end:
            data.append(end)

        if data:
            # duplicate and reimplement write() features here because of hl and
            # autoreset arguments

            data = self._empty.join(data)

            if self._can_autostrip:
                # hl and autoreset ignored in this case
                data = ansi_strip(data)
            else:
                # prepare arguments
                if hl is None:
                    if self._can_style and self._highlighter:
                        hl = self._highlighter
                elif hl is True:
                    if self._can_escape:  # override can_style
                        if self._highlighter:
                            hl = self._highlighter
                        else:
                            hl = select_highlighter(binary=self._is_binary)
                    else:
                        hl = None
                elif hl is False:
                    hl = None
                elif isinstance(hl, Highlighter):
                    if not self._can_escape:  # override can_style
                        hl = None
                else:
                    raise ValueError(f"hl type {type(hl)}")

                if autoreset is None:
                    autoreset = self._can_autoreset
                else:
                    autoreset = self._can_escape and autoreset

                # apply options
                if hl:
                    data = hl(data)

                if autoreset:
                    data = ansi_autoreset(data)

        # print(repr(data.encode()))  # TEST
        return data


def cprint(*objs, file=sys.stdout, **kwargs):
    """
    Convenience function to call `ColorationStream.print()` whithout having to
    ensure *file* is a `ColorationStream` object first.

    Other argument are the same than `ColorationStream.print()`.

    This function is faster if used after `wrap_std_streams()`, or if *file* is
    passed a `ColorationStream` object already.
    """
    try:
        print_method = file.print
        assert isinstance(file, ColorationStream)
    except AttributeError:
        file = ColorationStream(file, acquire=False)
        print_method = file.print

    print_method(*objs, **kwargs)
