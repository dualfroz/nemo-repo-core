import os
import time
import weakref

from gi.repository import Gio, GLib

from .Config import coreConfig
from .gitQuery import computeRepoInfo
from .logs import pluginLogger

logger = pluginLogger("cache")


class RepoCache:

    def __init__(self, ttlProvider):
        self._ttlProvider = ttlProvider
        self._entries = {}
        self._monitors = {}
        self._trackedFiles = {}
        self._invalidateCallbacks = []

    def get(self, repoRoot):
        now = time.monotonic()
        entry = self._entries.get(repoRoot)
        if entry is not None:
            info, storedAt = entry
            if (now - storedAt) < self._ttlProvider():
                return info
        return self.refresh(repoRoot)

    def refresh(self, repoRoot):
        info = computeRepoInfo(repoRoot)
        self._entries[repoRoot] = (info, time.monotonic())
        self._ensureWatch(repoRoot)
        return info

    def invalidate(self, repoRoot=None):
        if repoRoot is None:
            roots = list(self._entries)
            self._entries.clear()
        else:
            roots = [repoRoot] if self._entries.pop(repoRoot, None) else []
        for root in roots:
            self._notify(root)

    def registerFileObject(self, repoRoot, nemoFile):
        tracked = self._trackedFiles.setdefault(repoRoot, weakref.WeakSet())
        try:
            tracked.add(nemoFile)
        except TypeError:
            logger.debug("Object for %s is not weak-referenceable", repoRoot)

    def onInvalidate(self, callback):
        self._invalidateCallbacks.append(callback)

    def _notify(self, repoRoot):
        for nemoFile in list(self._trackedFiles.get(repoRoot, ())):
            nemoFile.invalidate_extension_info()
        for callback in list(self._invalidateCallbacks):
            callback(repoRoot)

    def _ensureWatch(self, repoRoot):
        if repoRoot in self._monitors:
            return
        gitDirectory = os.path.join(repoRoot, ".git")
        if not os.path.isdir(gitDirectory):
            return

        monitors = []
        for path in (gitDirectory, os.path.join(gitDirectory, "refs", "heads")):
            if not os.path.exists(path):
                continue
            try:
                gfile = Gio.File.new_for_path(path)
                monitor = gfile.monitor_directory(Gio.FileMonitorFlags.NONE, None)
            except GLib.Error as error:
                logger.debug("Cannot watch %s: %s", path, error)
                continue
            monitor.connect("changed", self._onGitDirectoryChanged, repoRoot)
            monitors.append(monitor)
        if monitors:
            self._monitors[repoRoot] = monitors

    def _onGitDirectoryChanged(self, monitor, gfile, otherFile, eventType, repoRoot):
        self._entries.pop(repoRoot, None)
        self._notify(repoRoot)


repoCache = RepoCache(lambda: coreConfig.ttlSeconds)
