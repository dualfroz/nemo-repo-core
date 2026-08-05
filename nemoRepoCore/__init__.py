"""nemo-repo-core: the shared foundation for repository-aware Nemo plugins.

A plugin is a single .py file in ~/.local/share/nemo-python/extensions/ that
imports this package and registers one Nemo provider. Everything expensive
or fiddly lives here: the config file, the git query layer, the cache that
keeps Nemo from forking git on every redraw, and the path handling that
turns a Nemo.FileInfo into something git can be pointed at.

Minimal plugin:

    from nemoRepoCore import (coreConfig, findRepoRoot, localDirectoryPath,
                              repoCache, requireCore)
    requireCore("0.1.0")

    coreConfig.registerDefaults({"indicators": {"mine": {"enabled": True}}})

    class MyProvider(GObject.GObject, Nemo.InfoProvider):
        def update_file_info(self, file):
            path = localDirectoryPath(file)
            if path is None:
                return
            root = findRepoRoot(path)
            if root is None:
                return
            repoCache.registerFileObject(root, file)
            info = repoCache.get(root)
            ...

Stability policy for everything listed in __all__:

  * The core is 0.x, so the API is not settled yet: any 0.x minor bump may
    remove or reshape anything. requireCore() knows this and treats the minor
    as the breaking component while the major is 0, so a plugin that asked
    for 0.1.0 refuses to load against 0.2.0 instead of misbehaving later.
  * From 1.0.0 on the usual guarantee applies: within a major version names
    are never removed and signatures only ever gain optional arguments, so a
    plugin that asked for 1.0.0 keeps working on 1.4.0, and only a major bump
    may reshape anything.
  * Names not in __all__, and anything with a leading underscore, are
    internal and may change in any release.

The public names are camelCase rather than PEP 8 snake_case on purpose: it is
the naming convention used across this author's projects. Only the methods
Nemo itself calls (update_file_info, get_columns and friends) keep the names
the file manager requires.
"""

from .Config import Config, coreConfig, coreDefaults, defaultConfigPath, legacyConfigPath
from .discovery import (findEnclosingRepoRoot, findRepoRoot, hasMarkerDirectory,
                        isRepoRoot, repoInfoFor)
from .gitQuery import computeRepoInfo, gitBinary, runGit
from .launchers import (editorAvailable, launchEditor, launchTerminal,
                        resolveTerminal)
from .logs import pluginLogger
from .nemoFiles import localDirectoryPath, localPath, singleLocalDirectory
from .RepoCache import RepoCache, repoCache
from .RepoInfo import LastCommit, RepoInfo
from .version import CoreVersionError, coreVersion, requireCore

__all__ = [
    "Config",
    "CoreVersionError",
    "LastCommit",
    "RepoCache",
    "RepoInfo",
    "computeRepoInfo",
    "coreConfig",
    "coreDefaults",
    "coreVersion",
    "defaultConfigPath",
    "editorAvailable",
    "findEnclosingRepoRoot",
    "findRepoRoot",
    "gitBinary",
    "hasMarkerDirectory",
    "isRepoRoot",
    "launchEditor",
    "launchTerminal",
    "legacyConfigPath",
    "localDirectoryPath",
    "localPath",
    "pluginLogger",
    "repoCache",
    "repoInfoFor",
    "requireCore",
    "resolveTerminal",
    "runGit",
    "singleLocalDirectory",
]
