import unittest

import support

from nemoRepoCore import LastCommit, RepoInfo


def makeInfo(**fields):
    info = RepoInfo("/repo")
    info.hasUpstream = True
    for name, value in fields.items():
        setattr(info, name, value)
    return info


class SummaryTests(unittest.TestCase):

    def testClean(self):
        self.assertEqual(makeInfo().summary, "clean")

    def testNoUpstream(self):
        self.assertEqual(makeInfo(hasUpstream=False).summary, "no upstream")

    def testAheadAndBehind(self):
        self.assertEqual(makeInfo(ahead=2, behind=1).summary, "2 ahead, 1 behind")

    def testChangedCountsStagedAndUnstaged(self):
        self.assertEqual(makeInfo(staged=1, unstaged=2).summary, "3 changed")

    def testUntrackedOnly(self):
        self.assertEqual(makeInfo(untracked=4).summary, "4 untracked")

    def testEverything(self):
        info = makeInfo(ahead=1, hasUpstream=True, staged=1, untracked=2)
        self.assertEqual(info.summary, "1 ahead, 1 changed, 2 untracked")

    def testNoUpstreamWithChanges(self):
        info = makeInfo(hasUpstream=False, unstaged=1, untracked=1)
        self.assertEqual(info.summary, "no upstream, 1 changed, 1 untracked")

    def testErrorReplacesSummary(self):
        self.assertEqual(makeInfo(error="git status failed", ahead=3).summary,
                         "git status failed")


class PropertyTests(unittest.TestCase):

    def testDefaults(self):
        info = RepoInfo()
        self.assertIsNone(info.root)
        self.assertIsNone(info.branch)
        self.assertIsNone(info.lastCommit)
        self.assertIsNone(info.error)
        self.assertEqual((info.ahead, info.behind), (0, 0))
        self.assertEqual((info.staged, info.unstaged, info.untracked), (0, 0, 0))
        self.assertFalse(info.hasUpstream)

    def testDirty(self):
        self.assertFalse(makeInfo().dirty)
        self.assertTrue(makeInfo(staged=1).dirty)
        self.assertTrue(makeInfo(unstaged=1).dirty)
        self.assertTrue(makeInfo(untracked=1).dirty)

    def testUnpushed(self):
        self.assertFalse(makeInfo().unpushed)
        self.assertTrue(makeInfo(ahead=1).unpushed)
        self.assertTrue(makeInfo(hasUpstream=False).unpushed)
        self.assertFalse(makeInfo(behind=3).unpushed)

    def testDetached(self):
        self.assertTrue(makeInfo(branch=None).detached)
        self.assertTrue(makeInfo(branch="(detached)").detached)
        self.assertFalse(makeInfo(branch="main").detached)

    def testBranchLabel(self):
        self.assertEqual(makeInfo(branch="feature/x").branchLabel, "feature/x")
        self.assertEqual(makeInfo(branch=None).branchLabel, "(detached)")

    def testSlotsRejectUnknownFields(self):
        with self.assertRaises(AttributeError):
            RepoInfo().unknownField = 1

    def testRepr(self):
        self.assertEqual(repr(makeInfo(branch="main")), "<RepoInfo /repo main: clean>")

    def testLastCommitFields(self):
        commit = LastCommit("abc1234", "Author", "2 hours ago", "subject")
        self.assertEqual(commit.hash, "abc1234")
        self.assertEqual(commit.author, "Author")
        self.assertEqual(commit.relativeDate, "2 hours ago")
        self.assertEqual(commit.subject, "subject")


if __name__ == "__main__":
    unittest.main()
