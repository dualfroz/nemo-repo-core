import os
import unittest

import support
from support import makeDirectory, makeRepository, requiresGit, writeFile

from nemoRepoCore import (findEnclosingRepoRoot, findRepoRoot, hasMarkerDirectory,
                          isRepoRoot, repoCache, repoInfoFor)


def makeFakeRepository(gitAsFile=False):
    root = makeDirectory()
    if gitAsFile:
        writeFile(root, ".git", "gitdir: /elsewhere\n")
    else:
        os.mkdir(os.path.join(root, ".git"))
    return root


class RootDetectionTests(unittest.TestCase):

    def testGitDirectoryIsRoot(self):
        self.assertTrue(isRepoRoot(makeFakeRepository()))

    def testGitFileIsRoot(self):
        self.assertTrue(isRepoRoot(makeFakeRepository(gitAsFile=True)))

    def testPlainDirectoryIsNotRoot(self):
        self.assertFalse(isRepoRoot(makeDirectory()))

    def testFindRepoRootOnlyChecksThePathItself(self):
        root = makeFakeRepository()
        nested = os.path.join(root, "src")
        os.mkdir(nested)
        self.assertEqual(findRepoRoot(root), root)
        self.assertIsNone(findRepoRoot(nested))


class EnclosingRootTests(unittest.TestCase):

    def testFindsRootFromNestedDirectory(self):
        root = makeFakeRepository()
        nested = os.path.join(root, "a", "b", "c")
        os.makedirs(nested)
        self.assertEqual(findEnclosingRepoRoot(nested), root)

    def testRootItself(self):
        root = makeFakeRepository()
        self.assertEqual(findEnclosingRepoRoot(root), root)

    def testNearestRootWins(self):
        outer = makeFakeRepository()
        inner = os.path.join(outer, "vendor", "lib")
        os.makedirs(os.path.join(inner, ".git"))
        self.assertEqual(findEnclosingRepoRoot(os.path.join(inner)), inner)

    def testOutsideAnyRepository(self):
        self.assertIsNone(findEnclosingRepoRoot(makeDirectory()))

    def testDepthLimit(self):
        root = makeFakeRepository()
        nested = os.path.join(root, "a", "b")
        os.makedirs(nested)
        self.assertIsNone(findEnclosingRepoRoot(nested, maximumDepth=2))
        self.assertEqual(findEnclosingRepoRoot(nested, maximumDepth=3), root)

    def testRelativePathIsResolved(self):
        root = makeFakeRepository()
        nested = os.path.join(root, "src")
        os.mkdir(nested)
        relative = os.path.relpath(nested)
        self.assertEqual(findEnclosingRepoRoot(relative), root)


class MarkerTests(unittest.TestCase):

    def testMarkerDirectory(self):
        path = makeDirectory()
        os.mkdir(os.path.join(path, ".venv"))
        self.assertTrue(hasMarkerDirectory(path, ".venv"))

    def testFileWithMarkerNameDoesNotCount(self):
        path = makeDirectory()
        writeFile(path, ".venv")
        self.assertFalse(hasMarkerDirectory(path, ".venv"))

    def testMissingMarker(self):
        self.assertFalse(hasMarkerDirectory(makeDirectory(), ".venv"))


@requiresGit
class RepoInfoForTests(unittest.TestCase):

    def setUp(self):
        repoCache.invalidate()

    def testRoot(self):
        repository = makeRepository()
        info = repoInfoFor(repository)
        self.assertEqual(info.root, repository)
        self.assertEqual(info.branch, "main")

    def testNestedWithoutWalkingUp(self):
        repository = makeRepository()
        nested = os.path.join(repository, "src")
        os.mkdir(nested)
        self.assertIsNone(repoInfoFor(nested))

    def testNestedWithWalkingUp(self):
        repository = makeRepository()
        nested = os.path.join(repository, "src")
        os.mkdir(nested)
        self.assertEqual(repoInfoFor(nested, walkUp=True).root, repository)

    def testOutsideRepository(self):
        self.assertIsNone(repoInfoFor(makeDirectory(), walkUp=True))


if __name__ == "__main__":
    unittest.main()
