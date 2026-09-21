import copy
import json
import os

from gi.repository import Gio, GLib

from .logs import applyLogLevel, pluginLogger

logger = pluginLogger("config")

configFileName = "nemo-repo-core.json"

coreDefaults = {
    "cache_ttl_seconds": 5,
    "editor_command": "code",
    "terminal_command": None,
    "log_level": "warning",
}


def configDirectory():
    return os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")


def defaultConfigPath():
    override = os.environ.get("NEMO_REPO_CORE_CONFIG")
    if override:
        return os.path.expanduser(override)
    return os.path.join(configDirectory(), configFileName)


def mergeDictionaries(base, overlay):
    merged = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = mergeDictionaries(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


class Config:

    def __init__(self, path=None):
        self.path = path or defaultConfigPath()
        self.defaults = copy.deepcopy(coreDefaults)
        self.userData = {}
        self.data = copy.deepcopy(self.defaults)
        self._changeCallbacks = []
        self._monitor = None
        self._createFileIfMissing()
        self.reload()
        self._watchFile()

    def registerDefaults(self, defaults):
        self.defaults = mergeDictionaries(self.defaults, defaults)
        self._recompute()

    def _recompute(self):
        self.data = mergeDictionaries(self.defaults, self.userData)
        applyLogLevel(self.data.get("log_level", "warning"))

    def section(self, name):
        value = self.data.get(name)
        return value if isinstance(value, dict) else {}

    def value(self, name, fallback=None):
        current = self.data.get(name)
        return fallback if current is None else current

    def flag(self, name, fallback=False):
        return bool(self.data.get(name, fallback))

    def sectionFlag(self, sectionName, key, fallback=False):
        entry = self.section(sectionName).get(key, fallback)
        if isinstance(entry, dict):
            return bool(entry.get("enabled", fallback))
        return bool(entry)

    @property
    def ttlSeconds(self):
        try:
            return max(0.0, float(self.data.get("cache_ttl_seconds", 5)))
        except (TypeError, ValueError):
            return 5.0

    @property
    def editorCommand(self):
        return self.data.get("editor_command") or "code"

    @property
    def terminalCommand(self):
        return self.data.get("terminal_command")

    def onChange(self, callback):
        self._changeCallbacks.append(callback)

    def _createFileIfMissing(self):
        if os.path.exists(self.path):
            return
        directory = os.path.dirname(self.path)
        try:
            os.makedirs(directory, exist_ok=True)
            with open(self.path, "w") as handle:
                json.dump(coreDefaults, handle, indent=2)
                handle.write("\n")
        except OSError as error:
            logger.warning("Could not create %s: %s", self.path, error)

    def reload(self):
        try:
            with open(self.path) as handle:
                loaded = json.load(handle)
        except FileNotFoundError:
            loaded = {}
        except (OSError, ValueError) as error:
            logger.warning("Ignoring unreadable config %s: %s", self.path, error)
            return
        self.userData = loaded if isinstance(loaded, dict) else {}
        self._recompute()
        for callback in list(self._changeCallbacks):
            callback()

    def _watchFile(self):
        try:
            gfile = Gio.File.new_for_path(self.path)
            self._monitor = gfile.monitor_file(Gio.FileMonitorFlags.NONE, None)
            self._monitor.connect("changed", self._onFileChanged)
        except GLib.Error as error:
            logger.warning("Config file will not live-reload: %s", error)

    def _onFileChanged(self, monitor, gfile, otherFile, eventType):
        if eventType in (Gio.FileMonitorEvent.CHANGES_DONE_HINT,
                         Gio.FileMonitorEvent.CREATED):
            self.reload()


coreConfig = Config()
