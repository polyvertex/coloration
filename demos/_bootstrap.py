import atexit
import contextlib
import os
import os.path
import shutil
import sys

# avoid bloating further the source tree with __pycache__ dirs,
# unless user specified -O
if not sys.flags.optimize:
    sys.dont_write_bytecode = True

# make sure ``import coloration`` in demos always finds local source first
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


# remove last remaining __pycache__ at exit :)
def _rmpycache():
    if pycache_dir:
        with contextlib.suppress(Exception):
            shutil.rmtree(pycache_dir, ignore_errors=True)


pycache_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "__pycache__")

if os.sep in pycache_dir:
    atexit.register(_rmpycache)
