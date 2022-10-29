# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT


class Highlighter:
    """Base abstract class for automatic text highlighting"""

    def __init__(self):
        super().__init__()

    def __call__(self, *args, **kwargs):
        return self.highlight(*args, **kwargs)

    def highlight(self, data):
        raise NotImplementedError
