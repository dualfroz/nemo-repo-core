"""The snapshot of a repository that every plugin reads."""

from collections import namedtuple

LastCommit = namedtuple("LastCommit", "hash author relativeDate subject")


class RepoInfo:
    """Everything one `git status` and one `git log -1` can tell us.

    Instances are immutable in practice: the cache hands the same object to
    every caller for the lifetime of a cache entry, so plugins must treat
    the fields as read-only.

    When `error` is set, every other field is at its zero value and must not
    be displayed as fact.
    """

    __slots__ = ("root", "branch", "upstream", "ahead", "behind", "hasUpstream",
                 "staged", "unstaged", "untracked", "lastCommit", "error")

    def __init__(self, root=None):
        self.root = root
        self.branch = None
        self.upstream = None
        self.ahead = 0
        self.behind = 0
        self.hasUpstream = False
        self.staged = 0
        self.unstaged = 0
        self.untracked = 0
        self.lastCommit = None
        self.error = None

    @property
    def dirty(self):
        return (self.staged + self.unstaged + self.untracked) > 0

    @property
    def unpushed(self):
        """Commits the remote does not have, including "there is no remote"."""
        return self.ahead > 0 or not self.hasUpstream

    @property
    def detached(self):
        return self.branch in (None, "(detached)")

    @property
    def branchLabel(self):
        return self.branch or "(detached)"

    @property
    def summary(self):
        """One ASCII line combining sync state and working tree state."""
        if self.error:
            return self.error
        parts = []
        if self.ahead:
            parts.append("%d ahead" % self.ahead)
        if self.behind:
            parts.append("%d behind" % self.behind)
        if not self.hasUpstream:
            parts.append("no upstream")
        treeParts = []
        if self.staged or self.unstaged:
            treeParts.append("%d changed" % (self.staged + self.unstaged))
        if self.untracked:
            treeParts.append("%d untracked" % self.untracked)
        if treeParts:
            parts.append(", ".join(treeParts))
        return ", ".join(parts) if parts else "clean"

    def __repr__(self):
        return "<RepoInfo %s %s: %s>" % (self.root, self.branchLabel, self.summary)
