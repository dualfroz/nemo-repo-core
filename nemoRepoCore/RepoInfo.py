from collections import namedtuple

LastCommit = namedtuple("LastCommit", "hash author relativeDate subject")


class RepoInfo:

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
        return self.ahead > 0 or not self.hasUpstream

    @property
    def detached(self):
        return self.branch in (None, "(detached)")

    @property
    def branchLabel(self):
        return self.branch or "(detached)"

    @property
    def summary(self):
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
