# nemo-repo-core

The shared foundation for repository-aware plugins for [Nemo](https://github.com/linuxmint/nemo),
the Cinnamon file manager.

Nemo can be extended in Python through `nemo-python`. Any extension that wants
to show something about a git repository ends up writing the same four things
before it can show anything at all: a config file, a way to call git without
blocking the file manager, a cache so git is not run once per icon per redraw,
and the path handling that turns a `Nemo.FileInfo` into a directory git can be
pointed at. That is roughly 400 lines before the first feature.

This package is those 400 lines, written once. A plugin built on it is a single
file that reads a repository state and draws something with it.

It is a library, not an extension. On its own it changes nothing about Nemo.

## Plugins built on it

| Plugin | What it adds |
| --- | --- |
| [nemo-repo-emblems](https://github.com/dualfroz/nemo-repo-emblems) | Emblem overlays: is a repository, dirty, unpushed, marker directories |
| [nemo-repo-columns](https://github.com/dualfroz/nemo-repo-columns) | "Git Branch" and "Git Status" columns in the list view |
| [nemo-repo-properties](https://github.com/dualfroz/nemo-repo-properties) | A "Git" tab in the folder Properties dialog |
| [nemo-repo-git-menu](https://github.com/dualfroz/nemo-repo-git-menu) | Right click git actions: status, log, fetch, pull |
| [nemo-folder-tools](https://github.com/dualfroz/nemo-folder-tools) | "Open Terminal Here" and "Open in Editor" for any folder |

Install only the ones you want. They share this core, so a folder is queried
once no matter how many of them are running.

## Requirements

- Nemo with `nemo-python` (Debian and Ubuntu based systems: `sudo apt install python-nemo`)
- Python 3.8 or newer, with PyGObject (`python3-gi`) and the Nemo typelib (`gir1.2-nemo-3.0`)
- `git` in `PATH`

## Install

```bash
git clone https://github.com/dualfroz/nemo-repo-core
cd nemo-repo-core
./install.sh
```

`install.sh` symlinks the package into `$XDG_DATA_HOME/nemo-repo-core`
(`~/.local/share/nemo-repo-core` by default) and verifies that it imports.
Nothing is written outside your home directory and no root is required.

Pass `--copy` to copy the package instead of linking it, which is what you want
if the checkout is temporary. `./uninstall.sh` removes it again.

If you prefer a normal Python install, `pip install --user .` also works; the
plugins find the core either way.

### Why not site-packages

Nemo loads extensions from `~/.local/share/nemo-python/extensions`, which is a
plain directory of scripts and not a package directory, so a plugin there
cannot import a library sitting next to it by accident. The core therefore
lives in its own version independent directory under `XDG_DATA_HOME`, and each
plugin locates it with a short bootstrap block (see below).

The alternative, dropping the package into
`~/.local/lib/python3.12/site-packages`, breaks the day the distribution moves
to Python 3.13: the interpreter stops looking in the old directory and every
plugin fails at once. A path that does not carry a Python version in it cannot
have that problem.

## Configuration

One file is shared by the core and every plugin:

```
~/.config/nemo-repo-core.json
```

It is created on first use and re-read within a second of being saved, so
changes take effect without restarting Nemo. Set `NEMO_REPO_CORE_CONFIG` to use
a different path.

Keys owned by the core:

| Key | Default | Meaning |
| --- | --- | --- |
| `cache_ttl_seconds` | `5` | How long a repository state may be reused before git is asked again |
| `editor_command` | `"code"` | Command used by plugins that open an editor |
| `terminal_command` | `null` | Terminal emulator to use; `null` means auto detect |
| `log_level` | `"warning"` | `debug`, `info`, `warning`, `error` |

Every plugin documents its own keys in its own README, and registers defaults
for them at load time, so an empty config file is a working config file. See
`config.example.json` for a file with the whole family's keys filled in.

Set `NEMO_REPO_LOG=debug` in the environment to raise the log level for one
Nemo session without editing the file. Messages go to stderr, which means the
terminal you started Nemo from.

### Migrating from the single file extension

Earlier versions of this project were one file, `nemo_repo_emblems.py`, with
its config in `~/.config/nemo-repo-emblems.json`. That file is still
understood: the first time a plugin loads and no `nemo-repo-core.json` exists,
the old file is copied over and the original is left untouched. Every key kept
its name, so nothing needs editing.

To switch over:

```bash
# 1. install the core and the plugins you want
./install.sh

# 2. remove the old extension, otherwise both run and everything is doubled
rm ~/.local/share/nemo-python/extensions/nemo_repo_emblems.py

# 3. restart the file manager
nemo -q
```

To go back, reinstall the old extension and remove the new plugins from
`~/.local/share/nemo-python/extensions`. The old config file was never modified
and is still there.

## Writing a plugin

A plugin is one `.py` file in `~/.local/share/nemo-python/extensions/` that
subclasses one of the `Nemo` provider interfaces. The core gives you the state;
you decide what to draw.

### 1. The bootstrap block

Copy this verbatim to the top of your plugin. It is the only part that knows
where the core lives, and it works whether the core was installed with
`install.sh` or with pip.

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

### 2. Declare the version you were built against

```python
from nemoRepoCore import requireCore
requireCore("0.1.0")
```

If the installed core is too old, or from a different incompatible series,
this raises and Nemo skips the extension with a clear message in the log
instead of loading a half working one. See "Versioning" for what counts as a
different series while the core is still `0.x`.

### 3. Register your defaults

```python
from nemoRepoCore import coreConfig

coreConfig.registerDefaults({
    "indicators": {
        "has_tests": {"enabled": True, "emblem": "emblem-ok", "marker_directory": "tests"},
    },
})
```

Defaults are merged under the user's file, never over it. Several plugins can
contribute keys to the same section.

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

`registerFileObject` is what makes emblems update by themselves: the core
watches `.git` and asks Nemo to re-query every registered file the moment a
commit, checkout or fetch changes something. Without it the display only
refreshes after the TTL expires.

`update_file_info` runs for every item Nemo draws. Keep it cheap: return early
for anything that is not a local directory, and never call git directly from
it. `findRepoRoot` costs one `stat`; `repoCache.get` costs nothing on a cache
hit.

A complete, working example is in `examples/nemoRepoLastCommit.py`: a "Last
Commit" column in about sixty lines.

### 5. Ship it

Give the file a name unlikely to collide, since Nemo imports every extension as
a top level module. Then link it into place and restart Nemo:

```bash
ln -s "$PWD/myPlugin.py" ~/.local/share/nemo-python/extensions/myPlugin.py
nemo -q
```

The five plugins listed above are all built exactly this way; their
`install.sh` scripts are a reasonable starting point to copy.

## API

Everything below is importable directly from `nemoRepoCore`.

### Repository state

| Name | Description |
| --- | --- |
| `repoCache.get(repoRoot)` | Cached `RepoInfo`. Recomputes when older than the TTL. |
| `repoCache.refresh(repoRoot)` | Recompute now, ignoring the TTL. For on demand views. |
| `repoCache.invalidate(repoRoot=None)` | Drop one entry, or all of them. |
| `repoCache.registerFileObject(repoRoot, nemoFile)` | Redraw this file when the repository changes. Weak reference. |
| `repoCache.onInvalidate(callback)` | `callback(repoRoot)` whenever an entry is dropped. |
| `computeRepoInfo(repoRoot)` | Uncached `RepoInfo`. The primitive behind the cache. |
| `runGit(arguments, cwd, timeoutSeconds=3)` | stdout as text, or `None` when git could not answer. |
| `gitBinary` | Absolute path to git, or `None` if it is not installed. |

`RepoInfo` fields: `root`, `branch`, `upstream`, `ahead`, `behind`,
`hasUpstream`, `staged`, `unstaged`, `untracked`, `lastCommit`, `error`.
Properties: `dirty`, `unpushed`, `detached`, `branchLabel`, `summary`.
`lastCommit` is a `LastCommit(hash, author, relativeDate, subject)` or `None`.
When `error` is set, treat every other field as unknown.

### Discovery

| Name | Description |
| --- | --- |
| `isRepoRoot(path)` | Does this directory itself hold `.git` (directory or worktree file). |
| `findRepoRoot(path)` | `path` if it is a repository root, else `None`. One stat, safe in hot paths. |
| `findEnclosingRepoRoot(path)` | Nearest repository root at or above `path`. For menus and other on demand work. |
| `hasMarkerDirectory(path, name)` | Does `path` directly contain a subdirectory `name`. |
| `repoInfoFor(path, walkUp=False)` | Cached `RepoInfo` for the repository at or above `path`, else `None`. |

### Nemo objects

| Name | Description |
| --- | --- |
| `localPath(nemoFile)` | Filesystem path, or `None` for anything not on `file://`. |
| `localDirectoryPath(nemoFile)` | Same, but `None` unless it is a directory. |
| `singleLocalDirectory(files)` | Path of the one selected local directory, else `None`. |

### Config, launching, logging

| Name | Description |
| --- | --- |
| `coreConfig.registerDefaults(defaults)` | Merge a plugin's defaults below the user's file. |
| `coreConfig.section(name)` | Merged sub-object, `{}` when absent. |
| `coreConfig.value(name, fallback=None)` | Top level value. |
| `coreConfig.flag(name, fallback=False)` | Top level boolean. |
| `coreConfig.sectionFlag(section, key, fallback=False)` | Boolean inside a section, accepting both `true` and `{"enabled": true}`. |
| `coreConfig.onChange(callback)` | Run after every reload of the file. |
| `coreConfig.ttlSeconds`, `.editorCommand`, `.terminalCommand`, `.path` | Core settings. |
| `resolveTerminal()` | Configured terminal, else the first one found. |
| `launchTerminal(path, shellCommand=None)` | Terminal in `path`, optionally running a command, shell stays open. |
| `launchEditor(path)` | Open `path` in the configured editor. |
| `editorAvailable()` | Is the configured editor actually installed. |
| `pluginLogger(name)` | Logger under the shared `nemo-repo` tree. |
| `requireCore(minimum)`, `coreVersion`, `CoreVersionError` | Version negotiation. |

## Versioning

Semantic versioning, enforced at load time by `requireCore`.

The core is at `0.1.0`, which in semver means the API is not settled yet: its
only consumers are the five plugins listed above and it has no outside users.
Until `1.0.0`, any minor bump may remove or rename anything in the API table.
`requireCore` follows the same rule and treats the minor as the breaking
component while the major is `0`, so a plugin that asked for `0.1.0` refuses to
load against `0.2.0` instead of breaking somewhere deeper.

From `1.0.0` on, the guarantee below is the written one and holds:

- Within a major version nothing in the API table is removed or renamed, and
  signatures only ever gain optional arguments. A plugin that asked for `1.0.0`
  keeps working on `1.4.0`.
- A major bump may change anything. `requireCore` refuses to run a plugin
  against a different major version, so the failure is loud and immediate
  rather than subtle.

Anything not in the API table, and anything with a leading underscore, is
internal either way.

## Tested on

Linux Mint 22.2 (Zara), Cinnamon 6.4.14, Nemo 6.4.5, python-nemo 6.4.0,
Python 3.12.3, PyGObject from `python3-gi`. It should work on any distribution
shipping Nemo with `nemo-python`; nothing here is Mint specific.

## Troubleshooting

**A plugin does nothing.** Nemo only loads extensions at startup: `nemo -q`,
then open a window. Check that the plugin is listed under Edit > Plugins.

**Nothing in the log.** Start Nemo from a terminal to see the messages:
`nemo -q; NEMO_REPO_LOG=debug nemo --no-desktop`.

**Emblems do not appear at all.** Nemo shows a limited number of emblems per
icon and prefers the ones you set by hand. Check that the icons were installed:
`ls ~/.local/share/icons/hicolor/scalable/emblems`.

**Everything is doubled.** The old single file extension is still installed
alongside the new plugins; see "Migrating from the single file extension".

## License

MIT. See `LICENSE`.
