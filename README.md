# nemo-repo-core

nemo-repo-core is a small Python library for writing repository-aware
extensions for [Nemo](https://github.com/linuxmint/nemo), the Cinnamon file
manager. It owns the parts every such extension needs before it can draw
anything: one shared config file, a git query layer that cannot block the file
manager for long, a cache that keeps Nemo from running git on every redraw, and
the path handling that turns a `Nemo.FileInfo` into a directory git can be
pointed at. It is a library, not an extension: on its own it changes nothing in
Nemo. The plugins listed below are built on it.

## Plugins

| Plugin | What it adds |
| --- | --- |
| nemo-repo-emblems | Emblem overlays: is a repository, has uncommitted changes, has unpushed commits, contains a marker directory or file |
| nemo-repo-columns | "Git Branch" and "Git Status" columns in the list view |
| nemo-repo-properties | A "Git" tab in the folder Properties dialog |
| nemo-repo-git-menu | Right click git actions: status, log, fetch, pull |
| nemo-folder-tools | "Open Terminal Here" and "Open in Editor" for any folder |

Each plugin is its own repository and needs this core installed. Install only
the ones you want; they share one cache, so a repository is queried once no
matter how many plugins are running.

## Features

- **Shared config file.** One JSON file for the core and all plugins,
  `$XDG_CONFIG_HOME/nemo-repo-core.json` (`~/.config/nemo-repo-core.json` by
  default), or the path in `NEMO_REPO_CORE_CONFIG`. It is created with the core
  defaults on first use and re-read whenever it is saved, so changes apply
  without restarting Nemo. An unreadable or invalid file is ignored with a
  warning and the last good values stay in effect.
- **Layered defaults.** Effective values are core defaults, then defaults
  registered by plugins, then the user's file, merged recursively. Several
  plugins can contribute keys to the same section, and an empty file is a
  working config.
- **Git query layer.** A repository state costs exactly two git calls:
  `git status --porcelain=2 --branch` and `git log -1`. Each call runs with
  `GIT_OPTIONAL_LOCKS=0` so it never takes the index lock, discards stderr, is
  capped at 3 seconds and never raises; a failure is reported in
  `RepoInfo.error` instead.
- **Repository state.** `RepoInfo` carries the branch, upstream, ahead and
  behind counts, staged, unstaged and untracked counts, the last commit (short
  hash, author, relative date, subject) and derived values: `dirty`,
  `unpushed`, `detached`, `branchLabel` and a one line `summary` such as
  `2 ahead, 3 changed, 1 untracked`.
- **Cache with live invalidation.** Results are cached per repository root for
  `cache_ttl_seconds`. The core watches `.git` and `.git/refs/heads`; any change
  there drops the entry at once and asks Nemo to re-query every file object a
  plugin registered for that repository, so a commit, checkout or fetch shows up
  without waiting for the TTL. File objects are held by weak reference.
- **Repository discovery.** `findRepoRoot` checks only the given directory (one
  `stat`, safe in `update_file_info`), `findEnclosingRepoRoot` walks up at most
  64 parent directories for on-demand work such as menus. A `.git` file
  (worktree or submodule) counts as a repository as well as a `.git` directory.
- **Nemo file helpers.** Convert a `Nemo.FileInfo` to a local path, a local
  directory path, or the single selected local directory; anything that is not
  on `file://` yields `None`.
- **Launchers.** Open a terminal in a directory, optionally running a command
  and leaving the shell open afterwards, and open a directory in the configured
  editor. The terminal is `terminal_command` if it is installed, otherwise the
  first one found of `gnome-terminal`, `x-terminal-emulator`, `tilix`,
  `konsole`, `xfce4-terminal`, `mate-terminal`, `kitty`, `alacritty`, `xterm`.
  Each known emulator is called with its own "run this command" flag; unknown
  ones get `-e`.
- **Logging.** All messages go to stderr under the `nemo-repo` logger tree.
  The level comes from `log_level`, and the `NEMO_REPO_LOG` environment
  variable overrides it.
- **Version negotiation.** `requireCore("0.1.0")` at plugin import time refuses
  to load a plugin against an incompatible core with a clear error, instead of
  letting it fail later.

## Requirements

- Nemo with `nemo-python` (Debian and Ubuntu based systems: `sudo apt install python-nemo`)
- Python 3.8 or newer with PyGObject (`python3-gi`) and the Nemo typelib (`gir1.2-nemo-3.0`)
- `git` in `PATH`

Tested on Linux Mint 22.2 with Cinnamon 6.4.14, Nemo 6.4.5, python-nemo 6.4.0
and Python 3.12.3. Nothing in the code is Mint specific.

## Install and run

From a checkout of this repository:

```bash
./install.sh
```

`install.sh` symlinks the `nemoRepoCore` package into
`$XDG_DATA_HOME/nemo-repo-core` (`~/.local/share/nemo-repo-core` by default),
checks that it imports and prints the core version. Pass `--copy` to copy the
package instead of linking it, for example when the checkout is temporary.
Nothing is written outside your home directory and no root is required.

`./uninstall.sh` removes the installed package and warns about plugins that are
still installed and now cannot load. Your config file is left in place.

A normal Python install also works, `pip install --user .`; plugins find the
core either way.

The core does nothing until at least one plugin is installed. After installing
plugins, restart Nemo with `nemo -q`.

### Why a separate directory and not site-packages

Nemo loads extensions from `~/.local/share/nemo-python/extensions`, a plain
directory of scripts. The core lives in its own directory under
`XDG_DATA_HOME` whose path does not contain a Python version, so a distribution
upgrade from one Python minor version to the next cannot orphan it the way it
would orphan a package in `~/.local/lib/python3.X/site-packages`. Each plugin
finds it with a short bootstrap block (see "Writing a plugin").

## Configuration

`config.example.json` is a complete file with the keys of the whole family. The
core owns these:

| Key | Default | Meaning |
| --- | --- | --- |
| `cache_ttl_seconds` | `5` | How long a repository state may be reused before git is asked again |
| `editor_command` | `"code"` | Command used to open a folder in an editor; may contain arguments separated by spaces |
| `terminal_command` | `null` | Terminal emulator; `null`, or a command that is not installed, means auto detect |
| `log_level` | `"warning"` | `debug`, `info`, `warning`, `error` or `critical` |

The other sections in the example belong to the plugins and are documented in
their READMEs:

| Section | Plugin |
| --- | --- |
| `indicators` | nemo-repo-emblems |
| `columns` | nemo-repo-columns |
| `actions.git_status`, `git_log`, `git_fetch`, `git_pull` | nemo-repo-git-menu |
| `actions.open_terminal`, `open_editor` | nemo-folder-tools |

To see log messages, start Nemo from a terminal with a raised level:

```bash
nemo -q; NEMO_REPO_LOG=debug nemo --no-desktop
```

## Writing a plugin

A plugin is one `.py` file in `~/.local/share/nemo-python/extensions/` that
subclasses one of the `Nemo` provider interfaces. `examples/nemoRepoLastCommit.py`
is a complete working plugin that adds a "Last Commit" column; copy it into the
extensions directory and run `nemo -q` to try it.

### 1. Bootstrap block

Put this at the top of the plugin. It makes the core importable whether it was
installed with `install.sh` (searched in `XDG_DATA_HOME`, then `XDG_DATA_DIRS`)
or with pip.

```python
import importlib.util
import os
import sys


def _ensureCoreOnPath():
    if importlib.util.find_spec("nemoRepoCore") is not None:
        return
    dataHome = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    dataDirs = (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":")
    for base in [dataHome] + dataDirs:
        candidate = os.path.join(base, "nemo-repo-core")
        if os.path.isdir(os.path.join(candidate, "nemoRepoCore")):
            sys.path.insert(0, candidate)
            return


_ensureCoreOnPath()
```

### 2. Declare the core version

```python
from nemoRepoCore import requireCore
requireCore("0.1.0")
```

If the installed core cannot serve that version, this raises
`CoreVersionError` and Nemo skips the extension.

### 3. Register defaults

```python
from nemoRepoCore import coreConfig

coreConfig.registerDefaults({
    "indicators": {
        "has_tests": {"enabled": True, "emblem": "emblem-ok", "marker_directory": "tests"},
    },
})
```

Defaults are merged below the user's file, never over it.

### 4. Read state and draw

```python
from nemoRepoCore import findRepoRoot, localDirectoryPath, repoCache


class MyProvider(GObject.GObject, Nemo.InfoProvider, Nemo.NameAndDescProvider):

    def update_file_info(self, file):
        path = localDirectoryPath(file)
        if path is None:
            return
        root = findRepoRoot(path)
        if root is None:
            return

        repoCache.registerFileObject(root, file)
        info = repoCache.get(root)
        if info.error:
            return
        if info.behind:
            file.add_emblem("emblem-important")

    def get_name_and_desc(self):
        return ["my-plugin:::What it does, shown in Nemo's plugin list"]
```

`update_file_info` runs for every item Nemo draws, so return early for anything
that is not a local directory and never call git directly from it.
`registerFileObject` is what makes the display update by itself when `.git`
changes.

### 5. Install it

Nemo imports every extension as a top level module, so pick a file name that
will not collide. Link it into place and restart Nemo:

```bash
ln -s "$PWD/myPlugin.py" ~/.local/share/nemo-python/extensions/myPlugin.py
nemo -q
```

## API

Everything below is importable from `nemoRepoCore` and listed in `__all__`.

### Repository state

| Name | Description |
| --- | --- |
| `repoCache.get(repoRoot)` | Cached `RepoInfo`, recomputed when older than the TTL |
| `repoCache.refresh(repoRoot)` | Recompute now, ignoring the TTL, and store the result |
| `repoCache.invalidate(repoRoot=None)` | Drop one entry, or all of them |
| `repoCache.registerFileObject(repoRoot, nemoFile)` | Re-query this file object when the repository changes (weak reference) |
| `repoCache.onInvalidate(callback)` | Call `callback(repoRoot)` whenever an entry is dropped |
| `RepoCache(ttlProvider)` | The cache class, for a private instance |
| `computeRepoInfo(repoRoot)` | Uncached `RepoInfo` |
| `runGit(arguments, cwd, timeoutSeconds=3)` | stdout as text, or `None` when git could not answer |
| `gitBinary` | Absolute path of git, or `None` |
| `RepoInfo`, `LastCommit` | State object and the `(hash, author, relativeDate, subject)` tuple |

`RepoInfo` fields: `root`, `branch`, `upstream`, `ahead`, `behind`,
`hasUpstream`, `staged`, `unstaged`, `untracked`, `lastCommit`, `error`.
Properties: `dirty`, `unpushed` (ahead of upstream, or no upstream at all),
`detached`, `branchLabel`, `summary`. When `error` is set, treat every other
field as unknown.

### Discovery

| Name | Description |
| --- | --- |
| `isRepoRoot(path)` | `path` holds `.git` as a directory or a file |
| `findRepoRoot(path)` | `path` if it is a repository root, else `None` |
| `findEnclosingRepoRoot(path, maximumDepth=64)` | Nearest repository root at or above `path`, else `None` |
| `hasMarkerDirectory(path, name)` | `path` directly contains a subdirectory `name` |
| `repoInfoFor(path, walkUp=False)` | Cached `RepoInfo` for the repository at (or with `walkUp`, above) `path`, else `None` |

### Nemo objects

| Name | Description |
| --- | --- |
| `localPath(nemoFile)` | Filesystem path, or `None` for anything not on `file://` |
| `localDirectoryPath(nemoFile)` | Same, but `None` unless it is a directory |
| `singleLocalDirectory(files)` | Path of the one selected local directory, else `None` |

### Config, launching, logging, versions

| Name | Description |
| --- | --- |
| `coreConfig` | The shared `Config` instance |
| `coreConfig.registerDefaults(defaults)` | Merge a plugin's defaults below the user's file |
| `coreConfig.section(name)` | Merged sub-object, `{}` when absent |
| `coreConfig.value(name, fallback=None)` | Top level value |
| `coreConfig.flag(name, fallback=False)` | Top level boolean |
| `coreConfig.sectionFlag(section, key, fallback=False)` | Boolean inside a section; accepts `true` and `{"enabled": true}` |
| `coreConfig.onChange(callback)` | Call `callback()` after every reload |
| `coreConfig.ttlSeconds`, `.editorCommand`, `.terminalCommand`, `.path` | Core settings |
| `Config(path=None)`, `coreDefaults`, `defaultConfigPath()` | Config class, core defaults and the config file location |
| `resolveTerminal()` | Configured terminal if installed, else the first one found, else `None` |
| `launchTerminal(path, shellCommand=None)` | Terminal in `path`, optionally running a command; returns `False` on failure |
| `launchEditor(path)` | Open `path` in the configured editor; returns `False` on failure |
| `editorAvailable()` | The configured editor command is in `PATH` |
| `pluginLogger(name)` | Logger under the shared `nemo-repo` tree |
| `requireCore(minimum)`, `coreVersion`, `CoreVersionError` | Version negotiation |

Names not in `__all__`, and names with a leading underscore, are internal.

### Versioning

Semantic versioning, enforced by `requireCore`. While the major version is `0`
the minor version is the breaking component: a plugin that asked for `0.1.0`
loads on `0.1.x` and refuses to load on `0.2.0`. From `1.0.0` on, the major
version is the breaking component and a plugin that asked for `1.0.0` loads on
any `1.x` at or above it.

### Naming

The API is camelCase. The methods Nemo calls on providers
(`update_file_info`, `get_columns`, `get_file_items` and so on) keep the names
Nemo requires, and config keys use snake_case JSON spelling.

## Tests

The tests use the standard library `unittest` and need PyGObject
(`python3-gi`). Run them from the repository root:

```bash
python3 -m unittest discover -s tests
```

They cover version negotiation, git status parsing and the `RepoInfo`
summary, config file handling with layered defaults, repository discovery, the
cache and its invalidation, terminal and editor argument building, and the Nemo
file helpers. Tests that need git create throwaway repositories (including a
bare remote for ahead and behind) in a temporary directory and are skipped when
`git` is not installed. The suite never touches your real config: the shared
config file is redirected to a temporary path and git runs with an empty global
config. Behaviour inside a running Nemo is checked by hand.

## Project layout

```
nemoRepoCore/
  __init__.py      public API (__all__)
  Config.py        shared config file, defaults, live reload
  RepoCache.py     TTL cache and .git watching
  RepoInfo.py      RepoInfo and LastCommit
  gitQuery.py      all git subprocess calls
  discovery.py     repository root detection
  nemoFiles.py     Nemo.FileInfo to local path
  launchers.py     terminal and editor launching
  logs.py          shared logger setup
  version.py       coreVersion and requireCore
examples/
  nemoRepoLastCommit.py   example "Last Commit" column plugin
tests/
  support.py              temporary config, git environment and repository helpers
  test*.py                unittest suites
config.example.json       config with every key of the family
install.sh, uninstall.sh  per-user install
pyproject.toml            metadata for pip install
```

## Limitations

- Linux only, and only Nemo with `nemo-python`.
- git runs synchronously in Nemo's main thread. Each call is capped at 3
  seconds, but a very large working tree can make a directory listing pause
  until the cache is warm.
- Live invalidation needs a `.git` directory. Worktrees and submodules, where
  `.git` is a file, are refreshed only when the TTL expires.
- Changes that do not touch `.git`, such as editing a tracked file or creating
  an untracked one, show up after the TTL, on the next redraw.
- `editor_command` and `terminal_command` are split on single spaces; quoted
  arguments are not supported.
- Cache entries and directory watches are kept for every repository seen until
  Nemo exits.
- The API is `0.x` and may change with any minor release.

## License

MIT. See `LICENSE`.
