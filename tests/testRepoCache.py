import gc
import unittest

import support
from support import (FakeNemoFile, commitFile, makeDirectory, makeRepository,
                     requiresGit, writeFile)

from nemoRepoCore import RepoCache


@requiresGit
class RepoCacheTests(unittest.TestCase):

    def setUp(self):
        self.ttl = 60.0
        self.cache = RepoCache(lambda: self.ttl)
        self.repository = makeRepository()

    def testGetReusesEntryWithinTtl(self):
        first = self.cache.get(self.repository)
        self.assertIs(self.cache.get(self.repository), first)

    def testCachedEntryHidesNewChangesUntilRefresh(self):
        self.assertFalse(self.cache.get(self.repository).dirty)
        writeFile(self.repository, "new.txt")
        self.assertFalse(self.cache.get(self.repository).dirty)
        self.assertTrue(self.cache.refresh(self.repository).dirty)
        self.assertTrue(self.cache.get(self.repository).dirty)

    def testZeroTtlRecomputesEveryTime(self):
        self.ttl = 0.0
        first = self.cache.get(self.repository)
        self.assertIsNot(self.cache.get(self.repository), first)

    def testInvalidateOneEntry(self):
        notified = []
        self.cache.onInvalidate(notified.append)
        first = self.cache.get(self.repository)
        self.cache.invalidate(self.repository)
        self.assertEqual(notified, [self.repository])
        self.assertIsNot(self.cache.get(self.repository), first)

    def testInvalidateUnknownEntryNotifiesNobody(self):
        notified = []
        self.cache.onInvalidate(notified.append)
        self.cache.invalidate(self.repository)
        self.assertEqual(notified, [])

    def testInvalidateEverything(self):
        other = makeRepository()
        notified = []
        self.cache.onInvalidate(notified.append)
        self.cache.get(self.repository)
        self.cache.get(other)
        self.cache.invalidate()
        self.assertEqual(sorted(notified), sorted([self.repository, other]))

    def testRegisteredFilesAreInvalidated(self):
        nemoFile = FakeNemoFile(self.repository)
        self.cache.registerFileObject(self.repository, nemoFile)
        self.cache.get(self.repository)
        self.cache.invalidate(self.repository)
        self.assertEqual(nemoFile.invalidations, 1)

    def testFilesOfOtherRepositoriesAreLeftAlone(self):
        other = makeRepository()
        nemoFile = FakeNemoFile(other)
        self.cache.registerFileObject(other, nemoFile)
        self.cache.get(self.repository)
        self.cache.invalidate(self.repository)
        self.assertEqual(nemoFile.invalidations, 0)

    def testRegisteredFilesAreWeakReferences(self):
        nemoFile = FakeNemoFile(self.repository)
        self.cache.registerFileObject(self.repository, nemoFile)
        del nemoFile
        gc.collect()
        self.assertEqual(len(self.cache._trackedFiles[self.repository]), 0)

    def testNonWeakReferenceableObjectIsIgnored(self):
        self.cache.registerFileObject(self.repository, 42)
        self.assertEqual(len(self.cache._trackedFiles[self.repository]), 0)

    def testGitDirectoryChangeDropsEntryAndNotifies(self):
        nemoFile = FakeNemoFile(self.repository)
        self.cache.registerFileObject(self.repository, nemoFile)
        first = self.cache.get(self.repository)
        self.cache._onGitDirectoryChanged(None, None, None, None, self.repository)
        self.assertEqual(nemoFile.invalidations, 1)
        self.assertIsNot(self.cache.get(self.repository), first)

    def testGitDirectoryIsWatched(self):
        self.cache.get(self.repository)
        self.assertIn(self.repository, self.cache._monitors)

    def testWatchIsCreatedOnce(self):
        self.cache.get(self.repository)
        monitors = self.cache._monitors[self.repository]
        self.cache.refresh(self.repository)
        self.assertIs(self.cache._monitors[self.repository], monitors)

    def testGitFileRepositoryIsNotWatched(self):
        worktree = makeDirectory()
        writeFile(worktree, ".git", "gitdir: /nonexistent\n")
        info = self.cache.get(worktree)
        self.assertIsNotNone(info.error)
        self.assertNotIn(worktree, self.cache._monitors)

    def testNewCommitIsVisibleAfterInvalidate(self):
        self.assertEqual(self.cache.get(self.repository).lastCommit.subject, "initial commit")
        commitFile(self.repository, "next.txt", "second commit")
        self.cache.invalidate(self.repository)
        self.assertEqual(self.cache.get(self.repository).lastCommit.subject, "second commit")


if __name__ == "__main__":
    unittest.main()
