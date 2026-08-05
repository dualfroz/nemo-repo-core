#!/usr/bin/python3
"""Example plugin: a "Last Commit" column for Nemo's list view.

Copy this file to ~/.local/share/nemo-python/extensions/ and restart Nemo
with `nemo -q` to try it. It is about sixty lines of real work because
nemo-repo-core already owns the config file, the git call and the cache.

The block above the imports is the core bootstrap. Copy it verbatim into
every plugin: it makes the plugin work whether the core was installed with
its install.sh or with pip, and it is the only piece that knows where the
core lives.
"""

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

import gi

gi.require_version("Nemo", "3.0")
from gi.repository import GObject, Nemo

from nemoRepoCore import (findRepoRoot, localDirectoryPath, repoCache,
                          requireCore)

requireCore("0.1.0")


class LastCommitColumnProvider(GObject.GObject, Nemo.ColumnProvider,
                               Nemo.InfoProvider, Nemo.NameAndDescProvider):

    def get_columns(self):
        return [
            Nemo.Column(name="NemoRepoExample::last_commit",
                        attribute="repo_last_commit",
                        label="Last Commit",
                        description="Subject and age of the most recent commit"),
        ]

    def update_file_info(self, file):
        path = localDirectoryPath(file)
        if path is None:
            return
        root = findRepoRoot(path)
        if root is None:
            file.add_string_attribute("repo_last_commit", "")
            return

        repoCache.registerFileObject(root, file)
        info = repoCache.get(root)
        if info.error or not info.lastCommit:
            file.add_string_attribute("repo_last_commit", "")
            return

        commit = info.lastCommit
        file.add_string_attribute("repo_last_commit",
                                  "%s (%s)" % (commit.subject, commit.relativeDate))

    def get_name_and_desc(self):
        return ["nemo-repo-example:::Example column showing the last commit"]
