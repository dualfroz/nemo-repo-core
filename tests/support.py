import atexit
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

repoRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
scratchRoot = tempfile.mkdtemp(prefix="nemo-repo-core-tests-")
atexit.register(shutil.rmtree, scratchRoot, True)

configPath = os.path.join(scratchRoot, "config", "nemo-repo-core.json")
gitConfigPath = os.path.join(scratchRoot, "gitconfig")
open(gitConfigPath, "w").close()

os.environ["NEMO_REPO_CORE_CONFIG"] = configPath
os.environ["NEMO_REPO_LOG"] = "critical"
os.environ["GIT_CONFIG_GLOBAL"] = gitConfigPath
os.environ["GIT_CONFIG_NOSYSTEM"] = "1"
os.environ["GIT_AUTHOR_NAME"] = "Test Author"
os.environ["GIT_AUTHOR_EMAIL"] = "author@example.com"
os.environ["GIT_COMMITTER_NAME"] = "Test Author"
os.environ["GIT_COMMITTER_EMAIL"] = "author@example.com"

sys.path.insert(0, repoRoot)

try:
    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio
except (ImportError, ValueError) as error:
    raise unittest.SkipTest("PyGObject is not available: %s" % error)

gitAvailable = shutil.which("git") is not None
requiresGit = unittest.skipUnless(gitAvailable, "git is not installed")


def makeDirectory():
    return tempfile.mkdtemp(dir=scratchRoot)


def runGitCommand(arguments, cwd):
    subprocess.run(["git"] + arguments, cwd=cwd, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def writeFile(directory, name, content="content\n"):
    path = os.path.join(directory, name)
    with open(path, "w") as handle:
        handle.write(content)
    return path


def commitFile(repository, name, message="change"):
    writeFile(repository, name, message + "\n")
    runGitCommand(["add", name], repository)
    runGitCommand(["commit", "-q", "-m", message], repository)


def makeRepository(withCommit=True):
    path = makeDirectory()
    runGitCommand(["init", "-q", "-b", "main"], path)
    if withCommit:
        commitFile(path, "readme.txt", "initial commit")
    return path


def makeClonedRepository():
    origin = makeDirectory()
    runGitCommand(["init", "-q", "--bare", "-b", "main"], origin)
    seed = makeRepository()
    runGitCommand(["remote", "add", "origin", origin], seed)
    runGitCommand(["push", "-q", "origin", "main"], seed)
    clone = makeDirectory()
    runGitCommand(["clone", "-q", origin, clone], clone)
    return seed, clone


def writeConfig(config, content):
    os.makedirs(os.path.dirname(config.path), exist_ok=True)
    with open(config.path, "w") as handle:
        json.dump(content, handle)
    config.reload()


class FakeNemoFile:

    def __init__(self, path, isDirectory=True, scheme="file"):
        self.path = path
        self.isDirectory = isDirectory
        self.scheme = scheme
        self.emblems = []
        self.attributes = {}
        self.invalidations = 0

    def get_uri_scheme(self):
        return self.scheme

    def get_uri(self):
        if self.scheme != "file":
            return "%s://example.com%s" % (self.scheme, self.path)
        return Gio.File.new_for_path(self.path).get_uri()

    def is_directory(self):
        return self.isDirectory

    def add_emblem(self, name):
        self.emblems.append(name)

    def add_string_attribute(self, name, value):
        self.attributes[name] = value

    def invalidate_extension_info(self):
        self.invalidations += 1
