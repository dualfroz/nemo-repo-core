import os

from .RepoCache import repoCache


def isRepoRoot(path):
    gitPath = os.path.join(path, ".git")
    return os.path.isdir(gitPath) or os.path.isfile(gitPath)


def findRepoRoot(path):
    return path if isRepoRoot(path) else None


def findEnclosingRepoRoot(path, maximumDepth=64):
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
    return os.path.isdir(os.path.join(path, name))


def repoInfoFor(path, walkUp=False):
    root = findEnclosingRepoRoot(path) if walkUp else findRepoRoot(path)
    if root is None:
        return None
    return repoCache.get(root)
