"""Everything that shells out to git lives here, and nowhere else."""

import os
import shutil
import subprocess

from .logs import pluginLogger
from .RepoInfo import LastCommit, RepoInfo

logger = pluginLogger("git")

gitBinary = shutil.which("git")

defaultTimeoutSeconds = 3


def runGit(arguments, cwd, timeoutSeconds=defaultTimeoutSeconds):
    """Run git and return stdout as text, or None when it could not run.

    Never raises and never blocks Nemo for long: stderr is discarded, index
    locks are avoided via GIT_OPTIONAL_LOCKS, and the call is capped by a
    timeout. A None result always means "no answer", never "empty answer".
    """
    if not gitBinary:
        return None
    environment = dict(os.environ)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        completed = subprocess.run(
            [gitBinary] + list(arguments),
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=environment,
            timeout=timeoutSeconds,
        )
    except (subprocess.TimeoutExpired, OSError) as error:
        logger.debug("git %s failed in %s: %s", " ".join(arguments), cwd, error)
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.decode("utf-8", "replace")


def _applyStatusLine(info, line):
    if line.startswith("# branch.head "):
        info.branch = line.split(" ", 2)[2]
    elif line.startswith("# branch.upstream "):
        info.upstream = line.split(" ", 2)[2]
        info.hasUpstream = True
    elif line.startswith("# branch.ab "):
        for token in line.split(" ")[2:]:
            if token.startswith("+"):
                info.ahead = int(token[1:])
            elif token.startswith("-"):
                info.behind = int(token[1:])
    elif line.startswith("1 ") or line.startswith("2 "):
        indexState, worktreeState = line.split(" ", 2)[1][:2]
        if indexState != ".":
            info.staged += 1
        if worktreeState != ".":
            info.unstaged += 1
    elif line.startswith("u "):
        info.staged += 1
    elif line.startswith("? "):
        info.untracked += 1


def computeRepoInfo(repoRoot):
    """Build a fresh RepoInfo for `repoRoot`, bypassing any cache.

    Plugins should normally call repoCache.get() instead; this is the
    uncached primitive behind it.
    """
    info = RepoInfo(repoRoot)
    if not gitBinary:
        info.error = "git not found in PATH"
        return info

    status = runGit(["status", "--porcelain=2", "--branch"], repoRoot)
    if status is None:
        info.error = "git status failed"
        return info

    for line in status.splitlines():
        _applyStatusLine(info, line)

    logLine = runGit(["log", "-1", "--format=%h%x09%an%x09%ar%x09%s"], repoRoot)
    if logLine:
        fields = logLine.strip("\n").split("\t")
        if len(fields) == 4:
            info.lastCommit = LastCommit(*fields)

    return info
