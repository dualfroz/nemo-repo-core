import logging
import os
import sys

_rootLogger = logging.getLogger("nemo-repo")
_handlerAttached = False

_levelNames = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "warn": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def _attachHandler():
    global _handlerAttached
    if _handlerAttached:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(name)s: %(levelname)s: %(message)s"))
    _rootLogger.addHandler(handler)
    _rootLogger.propagate = False
    _rootLogger.setLevel(_levelFromEnvironment())
    _handlerAttached = True


def _levelFromEnvironment():
    requested = os.environ.get("NEMO_REPO_LOG", "").strip().lower()
    return _levelNames.get(requested, logging.WARNING)


def applyLogLevel(name):
    _attachHandler()
    fromEnvironment = os.environ.get("NEMO_REPO_LOG", "").strip().lower()
    if fromEnvironment in _levelNames:
        _rootLogger.setLevel(_levelNames[fromEnvironment])
        return
    _rootLogger.setLevel(_levelNames.get(str(name).strip().lower(), logging.WARNING))


def pluginLogger(name):
    _attachHandler()
    return _rootLogger.getChild(name)
