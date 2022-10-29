# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import logging
import threading

# populated by bootstrap()
__all__ = [
    "NOTSET", "DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL",
    "NOTICE", "notice",
    "VERBOSE_THIRDPARTY_LOGGERS",
    "BaseLogger", "BaseLoggerAdapter",
    "CustomLoggerMixin", "Logger", "LoggerAdapter",
    "bootstrap",
    "get_logger", "getLogger",
    "has_logger", "patch_logger",
    "set_log_level"]


# forward standard log levels for convenience
CRITICAL = logging.CRITICAL
ERROR = logging.ERROR
WARNING = logging.WARNING
WARN = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG
NOTSET = logging.NOTSET

# custom log levels
# CAUTION: features implemented in this module must be updated according to any
# change made here
NOTICE = logging.INFO + 5  # highlighted info


# the list of third-party packages known to be way too verbose at DEBUG level
# the level of every logger referenced in this list will never go below INFO
VERBOSE_THIRDPARTY_LOGGERS = ["asyncio", "chardet.charsetprober", "urllib3"]


# keep trace of original logging classes and functions
# note: use getLoggerClass() instead of referencing the Logger class directly so
# to not undo any customization already involved
BaseLogger = logging.getLoggerClass()
BaseLoggerAdapter = logging.LoggerAdapter


_lock = threading.RLock()


class CustomLoggerMixin:
    def notice(self, msg, *args, **kwargs):
        # skip this method
        try:
            kwargs["stacklevel"] += 1
        except KeyError:
            kwargs["stacklevel"] = 2

        self.log(NOTICE, msg, *args, **kwargs)


class Logger(BaseLogger, CustomLoggerMixin):
    def __init__(self, *args, **kwargs):
        BaseLogger.__init__(self, *args, **kwargs)


class LoggerAdapter(BaseLoggerAdapter, CustomLoggerMixin):
    def __init__(self, logger, *args, **kwargs):
        assert isinstance(logger, Logger)
        BaseLoggerAdapter.__init__(self, logger, *args, **kwargs)


def bootstrap():
    """
    Install this module's `Logger` and `LoggerAdapter` classes (i.e.
    `logging.setLoggerClass()`), then forward not yet declared symbols from
    standard `logging` package in order to provide API compatibility.

    This function is called at import time already and is careful at not
    breaking any potential previous setup.
    """
    with _lock:
        # monkey-patch logging so that it uses our derived classes
        for sym_name in ("LoggerAdapter", ):
            orig_sym = getattr(logging, sym_name)
            custom_sym = globals()[sym_name]

            if orig_sym is globals()[f"Base{sym_name}"]:
                setattr(logging, sym_name, custom_sym)
            elif orig_sym is custom_sym:
                continue  # already patched
            elif issubclass(orig_sym, custom_sym):
                continue  # already patched, then derived by someone else
            else:
                raise RuntimeError(
                    f"someone already monkey-patched the logging package "
                    f"(at least symbol {sym_name})")

        # install own Logger class if needed
        if not issubclass(logging.getLoggerClass(), Logger):
            logging.setLoggerClass(Logger)

        # add custom log levels
        # ensure their respective id is not reserved by someone else already
        for level_name in ("NOTICE", ):
            level_id = globals()[level_name]
            installed_name = logging.getLevelName(level_id)
            if installed_name == level_name:
                continue

            if installed_name == f"Level {level_id}":  # default for unknown levels
                logging.addLevelName(level_id, level_name)
            else:
                raise RuntimeError(f"custom level {level_name} already reserved")

        # forward not yet declared symbols from the standard logging package in
        # order to provide API compatibility
        for sym_name in logging.__all__:
            if sym_name not in globals():
                try:
                    std_sym = getattr(logging, sym_name)
                except AttributeError:
                    continue
                else:
                    globals()[sym_name] = std_sym

            if sym_name not in __all__:
                __all__.append(sym_name)


def get_logger(name=None, **kwargs):
    """
    Same as `logging.getLogger`, but ensure the returned logger derives from
    `CustomLoggerMixin` as well by calling `patch_logger()`.

    For that reason, it is recommended to use this function instead of
    `logging.getLogger`.
    """
    with _lock:
        logger = logging.getLogger(name, **kwargs)
        logger = patch_logger(logger)
        return logger


#: Shorthand to `get_logger` for API compatibility
getLogger = get_logger


def has_logger(name):
    """Check if a logger designed by *name* already exists"""
    with _lock:
        if not name:
            raise ValueError("no name")
        return name in BaseLogger.manager.loggerDict


def patch_logger(logger):
    """
    Monkey-patch *logger* if instance does not derive already from
    `CustomLoggerMixin`.

    If needed, this function append `CustomLoggerMixin` as *logger* 's base
    class (i.e. to ``logger.__class__.__bases__``).

    Return *logger*.
    """
    with _lock:
        # this test includes our own Logger and LoggerAdapter classes already
        if not isinstance(logger, CustomLoggerMixin):
            if not isinstance(logger, (BaseLogger, BaseLoggerAdapter)):
                raise ValueError(f"logger type not supported: {type(logger)}")

            logger.__class__.__bases__ = tuple([
                *logger.__class__.__bases__,
                CustomLoggerMixin])

            if not isinstance(logger, CustomLoggerMixin):
                raise RuntimeError(
                    f"failed to patch logger of type: {type(logger)}")

        return logger


def set_log_level(new_level):
    """
    Apply log level *new_level* to the **root** logger.

    Same as ``logging.getLogger(None).setLevel(new_level)`` except this function
    ensures the log level of some third-party packages known to be way too
    verbose at DEBUG level, does not get set below INFO.
    """
    # some modules are known to be way too verbose
    special_level = INFO if new_level <= INFO else new_level
    for name in VERBOSE_THIRDPARTY_LOGGERS:
        logging.getLogger(name).setLevel(special_level)

    return get_logger(None).setLevel(new_level)


def notice(msg, *args, **kwargs):
    # skip this method
    try:
        kwargs["stacklevel"] += 2
    except KeyError:
        kwargs["stacklevel"] = 3

    logging.log(NOTICE, msg, *args, **kwargs)


bootstrap()
