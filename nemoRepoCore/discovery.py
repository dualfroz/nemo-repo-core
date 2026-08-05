"""Deciding whether a directory is a repository, and finding which one."""

import os

from .RepoCache import repoCache


def isRepoRoot(path):
    """True when `path` itself holds the repository.

    .git is a directory in a normal clone and a file in a worktree or
    submodule; both count.
    """
    gitPath = os.path.join(path, ".git")
    return os.path.isdir(gitPath) or os.path.isfile(gitPath)


def findRepoRoot(path):
    """Repository root, but only if `path` is that root. Cheap: one stat.

    This is what emblem and column plugins want, because they run for every
    folder Nemo draws and must not walk the filesystem upwards.
    """
    return path if isRepoRoot(path) else None


def findEnclosingRepoRoot(path, maximumDepth=64):
    """Nearest repository root at or above `path`, or None.

    For on-demand work such as a context menu, where walking a handful of
    parent directories is free and the user expects git actions to work from
    anywhere inside their checkout.
    """
    current = os.path.abspath(path)
    for _ in range(maximumDepth):
        if isRepoRoot(current):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent
    return None


def hasMarkerDirectory(path, name):
    """True when `path` directly contains a subdirectory called `name`."""
    return os.path.isdir(os.path.join(path, name))


def repoInfoFor(path, walkUp=False):
    """Cached RepoInfo for the repository at (or above) `path`, else None."""
    root = findEnclosingRepoRoot(path) if walkUp else findRepoRoot(path)
    if root is None:
        return None
    return repoCache.get(root)
