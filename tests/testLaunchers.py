import unittest
from unittest import mock

import support
from support import writeConfig

from nemoRepoCore import (coreConfig, editorAvailable, launchEditor, launchTerminal,
                          launchers, resolveTerminal)

shellTail = "; exec \"${SHELL:-bash}\""


def installedOnly(*names):
    return lambda command: "/usr/bin/" + command if command in names else None


class LauncherTestCase(unittest.TestCase):

    def setUp(self):
        self.whichPatch = mock.patch.object(launchers.shutil, "which")
        self.popenPatch = mock.patch.object(launchers.subprocess, "Popen")
        self.which = self.whichPatch.start()
        self.popen = self.popenPatch.start()
        self.addCleanup(self.whichPatch.stop)
        self.addCleanup(self.popenPatch.stop)
        self.addCleanup(writeConfig, coreConfig, {})

    def configure(self, **settings):
        writeConfig(coreConfig, settings)

    def install(self, *names):
        self.which.side_effect = installedOnly(*names)


class ResolveTerminalTests(LauncherTestCase):

    def testConfiguredTerminalWins(self):
        self.configure(terminal_command="myterm --hold")
        self.install("myterm", "gnome-terminal")
        self.assertEqual(resolveTerminal(), "myterm --hold")

    def testMissingConfiguredTerminalFallsBack(self):
        self.configure(terminal_command="myterm")
        self.install("konsole", "xterm")
        self.assertEqual(resolveTerminal(), "konsole")

    def testCandidateOrder(self):
        self.install("xterm", "gnome-terminal")
        self.assertEqual(resolveTerminal(), "gnome-terminal")

    def testNothingInstalled(self):
        self.install()
        self.assertIsNone(resolveTerminal())


class LaunchTerminalTests(LauncherTestCase):

    def expectedScript(self, path, command):
        return "cd %s && %s%s" % (path, command, shellTail)

    def testCommandFlagPerEmulator(self):
        cases = {
            "gnome-terminal": ["--"],
            "mate-terminal": ["--"],
            "tilix": ["-e"],
            "konsole": ["-e"],
            "xfce4-terminal": ["-x"],
            "kitty": [],
            "alacritty": ["-e"],
            "xterm": ["-e"],
            "x-terminal-emulator": ["-e"],
        }
        for terminal, flags in cases.items():
            with self.subTest(terminal=terminal):
                self.install(terminal)
                self.popen.reset_mock()
                self.assertTrue(launchTerminal("/work", "git status"))
                arguments = self.popen.call_args.args[0]
                self.assertEqual(arguments, [terminal] + flags + [
                    "bash", "-c", self.expectedScript("'/work'", "git status")])
                self.assertEqual(self.popen.call_args.kwargs["cwd"], "/work")

    def testPathIsShellQuoted(self):
        self.install("xterm")
        launchTerminal("/work/it's here", "git log")
        script = self.popen.call_args.args[0][-1]
        self.assertEqual(script, self.expectedScript("'/work/it'\\''s here'", "git log"))

    def testUnknownTerminalUsesDashE(self):
        self.configure(terminal_command="/opt/bin/myterm --class repo")
        self.install("/opt/bin/myterm")
        launchTerminal("/work", "git pull")
        self.assertEqual(self.popen.call_args.args[0][:4],
                         ["/opt/bin/myterm", "--class", "repo", "-e"])

    def testAbsoluteKnownTerminalUsesItsFlag(self):
        self.configure(terminal_command="/usr/bin/gnome-terminal")
        self.install("/usr/bin/gnome-terminal")
        launchTerminal("/work", "git status")
        self.assertEqual(self.popen.call_args.args[0][:2], ["/usr/bin/gnome-terminal", "--"])

    def testWithoutCommandOnlyStartsTerminal(self):
        self.install("konsole")
        self.assertTrue(launchTerminal("/work"))
        self.popen.assert_called_once_with(["konsole"], cwd="/work")

    def testNoTerminalFound(self):
        self.install()
        self.assertFalse(launchTerminal("/work", "git status"))
        self.popen.assert_not_called()

    def testStartFailure(self):
        self.install("xterm")
        self.popen.side_effect = OSError("broken")
        self.assertFalse(launchTerminal("/work"))


class EditorTests(LauncherTestCase):

    def testEditorWithArguments(self):
        self.configure(editor_command="code -n")
        self.install("code")
        self.assertTrue(launchEditor("/work"))
        self.popen.assert_called_once_with(["code", "-n", "/work"])

    def testDefaultEditorIsCode(self):
        self.install("code")
        launchEditor("/work")
        self.popen.assert_called_once_with(["code", "/work"])

    def testMissingEditor(self):
        self.configure(editor_command="subl")
        self.install("code")
        self.assertFalse(launchEditor("/work"))
        self.popen.assert_not_called()

    def testEditorStartFailure(self):
        self.install("code")
        self.popen.side_effect = OSError("broken")
        self.assertFalse(launchEditor("/work"))

    def testEditorAvailable(self):
        self.configure(editor_command="zed --new")
        self.install("zed")
        self.assertTrue(editorAvailable())
        self.install("code")
        self.assertFalse(editorAvailable())


if __name__ == "__main__":
    unittest.main()
