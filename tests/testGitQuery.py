import os
import unittest
from unittest import mock

import support
from support import (commitFile, makeClonedRepository, makeDirectory,
                     makeRepository, requiresGit, runGitCommand, writeFile)

from nemoRepoCore import RepoInfo, computeRepoInfo, gitQuery, runGit
from nemoRepoCore.gitQuery import _applyStatusLine


def parseLines(lines):
    info = RepoInfo("/repo")
    for line in lines:
        _applyStatusLine(info, line)
    return info


class StatusParsingTests(unittest.TestCase):

    def testBranchHead(self):
        self.assertEqual(parseLines(["# branch.head feature/x"]).branch, "feature/x")

    def testDetachedHead(self):
        info = parseLines(["# branch.head (detached)"])
        self.assertEqual(info.branch, "(detached)")
        self.assertTrue(info.detached)

    def testUpstream(self):
        info = parseLines(["# branch.upstream origin/main"])
        self.assertEqual(info.upstream, "origin/main")
        self.assertTrue(info.hasUpstream)

    def testAheadBehind(self):
        info = parseLines(["# branch.ab +3 -2"])
        self.assertEqual((info.ahead, info.behind), (3, 2))

    def testOrdinaryChanges(self):
        info = parseLines([
            "1 M. N... 100644 100644 100644 aaa bbb staged.txt",
            "1 .M N... 100644 100644 100644 aaa bbb unstaged.txt",
            "1 MM N... 100644 100644 100644 aaa bbb both.txt",
        ])
        self.assertEqual((info.staged, info.unstaged), (2, 2))

    def testRenameCountsAsStaged(self):
        info = parseLines(["2 R. N... 100644 100644 100644 aaa bbb R100 new.txt\told.txt"])
        self.assertEqual((info.staged, info.unstaged), (1, 0))

    def testUnmergedCountsAsStaged(self):
        info = parseLines(["u UU N... 100644 100644 100644 100644 a b c conflict.txt"])
        self.assertEqual(info.staged, 1)

    def testUntracked(self):
        info = parseLines(["? one.txt", "? two.txt"])
        self.assertEqual(info.untracked, 2)

    def testIgnoredAndOidLinesAreSkipped(self):
        info = parseLines(["# branch.oid 0123456789", "! ignored.txt"])
        self.assertEqual(info.summary, "no upstream")
        self.assertFalse(info.dirty)


@requiresGit
class ComputeRepoInfoTests(unittest.TestCase):

    def testFreshRepositoryWithoutUpstream(self):
        repository = makeRepository()
        info = computeRepoInfo(repository)
        self.assertIsNone(info.error)
        self.assertEqual(info.root, repository)
        self.assertEqual(info.branch, "main")
        self.assertFalse(info.hasUpstream)
        self.assertEqual(info.summary, "no upstream")
        self.assertTrue(info.unpushed)

    def testLastCommit(self):
        repository = makeRepository()
        commit = computeRepoInfo(repository).lastCommit
        self.assertEqual(commit.subject, "initial commit")
        self.assertEqual(commit.author, "Test Author")
        self.assertGreaterEqual(len(commit.hash), 7)
        self.assertTrue(commit.relativeDate)

    def testRepositoryWithoutCommits(self):
        repository = makeRepository(withCommit=False)
        info = computeRepoInfo(repository)
        self.assertIsNone(info.error)
        self.assertEqual(info.branch, "main")
        self.assertIsNone(info.lastCommit)

    def testWorkingTreeCounts(self):
        repository = makeRepository()
        commitFile(repository, "second.txt", "second")
        writeFile(repository, "readme.txt", "modified\n")
        writeFile(repository, "second.txt", "staged\n")
        runGitCommand(["add", "second.txt"], repository)
        writeFile(repository, "new.txt")
        info = computeRepoInfo(repository)
        self.assertEqual((info.staged, info.unstaged, info.untracked), (1, 1, 1))
        self.assertTrue(info.dirty)
        self.assertEqual(info.summary, "no upstream, 2 changed, 1 untracked")

    def testDetachedHead(self):
        repository = makeRepository()
        runGitCommand(["checkout", "-q", "--detach"], repository)
        info = computeRepoInfo(repository)
        self.assertTrue(info.detached)
        self.assertEqual(info.branchLabel, "(detached)")

    def testCloneTracksUpstream(self):
        seed, clone = makeClonedRepository()
        info = computeRepoInfo(clone)
        self.assertTrue(info.hasUpstream)
        self.assertEqual(info.upstream, "origin/main")
        self.assertEqual(info.summary, "clean")
        self.assertFalse(info.unpushed)

    def testAheadOfUpstream(self):
        seed, clone = makeClonedRepository()
        commitFile(clone, "local.txt", "local work")
        info = computeRepoInfo(clone)
        self.assertEqual((info.ahead, info.behind), (1, 0))
        self.assertTrue(info.unpushed)
        self.assertEqual(info.summary, "1 ahead")

    def testBehindUpstream(self):
        seed, clone = makeClonedRepository()
        commitFile(seed, "remote.txt", "remote work")
        runGitCommand(["push", "-q", "origin", "main"], seed)
        runGitCommand(["fetch", "-q"], clone)
        info = computeRepoInfo(clone)
        self.assertEqual((info.ahead, info.behind), (0, 1))
        self.assertEqual(info.summary, "1 behind")

    def testDirectoryOutsideRepository(self):
        info = computeRepoInfo(makeDirectory())
        self.assertEqual(info.error, "git status failed")
        self.assertEqual(info.summary, "git status failed")


class MissingGitTests(unittest.TestCase):

    def testComputeReportsMissingGit(self):
        with mock.patch.object(gitQuery, "gitBinary", None):
            info = computeRepoInfo(makeDirectory())
        self.assertEqual(info.error, "git not found in PATH")

    def testRunGitReturnsNoneWithoutGit(self):
        with mock.patch.object(gitQuery, "gitBinary", None):
            self.assertIsNone(runGit(["status"], makeDirectory()))


@requiresGit
class RunGitTests(unittest.TestCase):

    def testReturnsStdout(self):
        repository = makeRepository()
        self.assertEqual(runGit(["rev-parse", "--abbrev-ref", "HEAD"], repository), "main\n")

    def testFailureReturnsNone(self):
        self.assertIsNone(runGit(["rev-parse", "HEAD"], makeDirectory()))

    def testMissingDirectoryReturnsNone(self):
        missing = os.path.join(makeDirectory(), "missing")
        self.assertIsNone(runGit(["status"], missing))

    def testOptionalLocksAreDisabled(self):
        with mock.patch.object(gitQuery.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=0, stdout=b"")
            runGit(["status"], support.scratchRoot)
        environment = run.call_args.kwargs["env"]
        self.assertEqual(environment["GIT_OPTIONAL_LOCKS"], "0")
        self.assertEqual(run.call_args.kwargs["timeout"], 3)


if __name__ == "__main__":
    unittest.main()
