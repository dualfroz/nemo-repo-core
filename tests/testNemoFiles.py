import os
import unittest

import support
from support import FakeNemoFile, makeDirectory

from nemoRepoCore import localDirectoryPath, localPath, singleLocalDirectory


class LocalPathTests(unittest.TestCase):

    def testLocalFile(self):
        path = os.path.join(makeDirectory(), "file.txt")
        self.assertEqual(localPath(FakeNemoFile(path, isDirectory=False)), path)

    def testPathWithSpacesAndNonAsciiCharacters(self):
        path = os.path.join(makeDirectory(), "my folder " + chr(0xe9))
        self.assertEqual(localPath(FakeNemoFile(path)), path)

    def testRemoteLocation(self):
        self.assertIsNone(localPath(FakeNemoFile("/share", scheme="sftp")))


class LocalDirectoryTests(unittest.TestCase):

    def testDirectory(self):
        path = makeDirectory()
        self.assertEqual(localDirectoryPath(FakeNemoFile(path)), path)

    def testRegularFile(self):
        path = os.path.join(makeDirectory(), "file.txt")
        self.assertIsNone(localDirectoryPath(FakeNemoFile(path, isDirectory=False)))

    def testRemoteDirectory(self):
        self.assertIsNone(localDirectoryPath(FakeNemoFile("/share", scheme="smb")))


class SingleSelectionTests(unittest.TestCase):

    def testOneDirectory(self):
        path = makeDirectory()
        self.assertEqual(singleLocalDirectory([FakeNemoFile(path)]), path)

    def testNoSelection(self):
        self.assertIsNone(singleLocalDirectory([]))

    def testSeveralDirectories(self):
        files = [FakeNemoFile(makeDirectory()), FakeNemoFile(makeDirectory())]
        self.assertIsNone(singleLocalDirectory(files))

    def testOneFile(self):
        path = os.path.join(makeDirectory(), "file.txt")
        self.assertIsNone(singleLocalDirectory([FakeNemoFile(path, isDirectory=False)]))


if __name__ == "__main__":
    unittest.main()
