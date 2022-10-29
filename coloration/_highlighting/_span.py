# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import itertools


try:
    _pairwise = itertools.pairwise  # 3.10
except AttributeError:
    def _pairwise(iterable):
        a, b = itertools.tee(iterable)
        next(b, None)
        return zip(a, b)


class HighlighterSpan:
    __slots__ = ("_start", "_end", "_data")

    def __init__(self, start, end, data=None):
        assert isinstance(start, int)
        assert isinstance(end, int)
        assert start >= 0
        assert end > 0
        assert start < end

        self._start = start
        self._end = end
        self._data = data

    def __repr__(self):
        return "<{} [{}:{}] data={!r}>".format(
            self.__class__.__name__, self._start, self._end, self._data)

    def __lt__(self, other):
        if not isinstance(other, HighlighterSpan):
            raise TypeError(f"not supported type: {type(other)}")
        return self._start < other._start

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def data(self):
        return self._data


class HighlighterRegion:
    __slots__ = ("_start", "_end", "_spans")

    def __init__(self, start, end):
        assert isinstance(start, int)
        assert isinstance(end, int)
        assert start >= 0
        assert end > 0
        assert start < end

        self._start = start
        self._end = end
        self._spans = []

    def __iter__(self):
        if not self._spans:
            yield HighlighterSpan(self._start, self._end)
        else:
            spans = self._spans[:]

            if self._start < spans[0].start:
                yield HighlighterSpan(self._start, spans[0].start)

            if len(spans) == 1:
                yield spans[0]
            else:
                first = True
                for span1, span2 in _pairwise(spans):
                    if first:
                        yield span1
                        first = False
                    if span1.end < span2.start:
                        yield HighlighterSpan(span1.end, span2.start)
                    yield span2

            if spans[-1].end < self._end:
                yield HighlighterSpan(spans[-1].end, self._end)

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    def insert_span(self, newspan):
        nstart = newspan.start
        for idx, span in enumerate(self._spans):
            if nstart < span.start:
                self._spans.insert(idx, newspan)
                return
        self._spans.append(newspan)
