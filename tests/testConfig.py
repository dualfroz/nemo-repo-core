import json
import logging
import os
import unittest
from unittest import mock

import support
from support import makeDirectory, writeConfig

from nemoRepoCore import Config, coreConfig, coreDefaults, defaultConfigPath
from nemoRepoCore.Config import mergeDictionaries
from nemoRepoCore.logs import _rootLogger, applyLogLevel


def makeConfig(content=None):
    path = os.path.join(makeDirectory(), "nested", "config.json")
    if content is not None:
        os.makedirs(os.path.dirname(path))
        with open(path, "w") as handle:
            json.dump(content, handle)
    return Config(path)


class MergeTests(unittest.TestCase):

    def testOverlayWins(self):
        self.assertEqual(mergeDictionaries({"a": 1, "b": 2}, {"b": 3}), {"a": 1, "b": 3})

    def testNestedDictionariesMerge(self):
        merged = mergeDictionaries({"s": {"a": 1, "b": 2}}, {"s": {"b": 3, "c": 4}})
        self.assertEqual(merged, {"s": {"a": 1, "b": 3, "c": 4}})

    def testNonDictionaryReplacesDictionary(self):
        self.assertEqual(mergeDictionaries({"s": {"a": 1}}, {"s": False}), {"s": False})

    def testInputsAreNotModified(self):
        base = {"s": {"a": 1}}
        overlay = {"s": {"b": 2}}
        merged = mergeDictionaries(base, overlay)
        merged["s"]["a"] = 99
        self.assertEqual(base, {"s": {"a": 1}})
        self.assertEqual(overlay, {"s": {"b": 2}})


class ConfigFileTests(unittest.TestCase):

    def testMissingFileIsCreatedWithCoreDefaults(self):
        config = makeConfig()
        with open(config.path) as handle:
            self.assertEqual(json.load(handle), coreDefaults)
        self.assertEqual(config.data, coreDefaults)

    def testExistingFileIsNotOverwritten(self):
        config = makeConfig({"editor_command": "vim"})
        with open(config.path) as handle:
            self.assertEqual(json.load(handle), {"editor_command": "vim"})

    def testUserValuesOverrideCoreDefaults(self):
        config = makeConfig({"cache_ttl_seconds": 1})
        self.assertEqual(config.ttlSeconds, 1.0)
        self.assertEqual(config.editorCommand, "code")

    def testPluginDefaultsSitBelowUserValues(self):
        config = makeConfig({"actions": {"git_log": False}})
        config.registerDefaults({"actions": {"git_log": True, "git_pull": True}})
        self.assertEqual(config.section("actions"), {"git_log": False, "git_pull": True})

    def testDefaultsFromSeveralPluginsMerge(self):
        config = makeConfig({})
        config.registerDefaults({"actions": {"open_terminal": True}})
        config.registerDefaults({"actions": {"git_status": True}})
        self.assertEqual(config.section("actions"), {"open_terminal": True, "git_status": True})

    def testReloadPicksUpChanges(self):
        config = makeConfig({})
        writeConfig(config, {"terminal_command": "xterm"})
        self.assertEqual(config.terminalCommand, "xterm")

    def testInvalidJsonKeepsPreviousValues(self):
        config = makeConfig({"editor_command": "vim"})
        with open(config.path, "w") as handle:
            handle.write("{ not json")
        config.reload()
        self.assertEqual(config.editorCommand, "vim")

    def testNonObjectJsonIsTreatedAsEmpty(self):
        config = makeConfig(["not", "an", "object"])
        self.assertEqual(config.data, coreDefaults)

    def testDeletedFileFallsBackToDefaults(self):
        config = makeConfig({"editor_command": "vim"})
        os.remove(config.path)
        config.reload()
        self.assertEqual(config.editorCommand, "code")

    def testOnChangeRunsAfterReload(self):
        config = makeConfig({})
        calls = []
        config.onChange(lambda: calls.append(config.terminalCommand))
        writeConfig(config, {"terminal_command": "kitty"})
        self.assertEqual(calls, ["kitty"])

    def testOnChangeSkippedForUnreadableFile(self):
        config = makeConfig({})
        calls = []
        config.onChange(lambda: calls.append(True))
        with open(config.path, "w") as handle:
            handle.write("[")
        config.reload()
        self.assertEqual(calls, [])


class AccessorTests(unittest.TestCase):

    def setUp(self):
        self.config = makeConfig({
            "number": 0,
            "nothing": None,
            "switch": True,
            "plain": {"on": True, "off": False},
            "nested": {"on": {"enabled": True}, "off": {"enabled": False}, "bare": {}},
            "notSection": 5,
        })

    def testSectionReturnsDictionary(self):
        self.assertEqual(self.config.section("plain"), {"on": True, "off": False})

    def testSectionIsEmptyForMissingOrNonDictionary(self):
        self.assertEqual(self.config.section("missing"), {})
        self.assertEqual(self.config.section("notSection"), {})

    def testValueFallsBackOnlyForNone(self):
        self.assertEqual(self.config.value("number", 7), 0)
        self.assertEqual(self.config.value("nothing", 7), 7)
        self.assertEqual(self.config.value("missing", 7), 7)

    def testFlag(self):
        self.assertTrue(self.config.flag("switch"))
        self.assertFalse(self.config.flag("missing"))
        self.assertTrue(self.config.flag("missing", True))

    def testSectionFlagWithBooleans(self):
        self.assertTrue(self.config.sectionFlag("plain", "on"))
        self.assertFalse(self.config.sectionFlag("plain", "off"))

    def testSectionFlagWithEnabledObjects(self):
        self.assertTrue(self.config.sectionFlag("nested", "on"))
        self.assertFalse(self.config.sectionFlag("nested", "off"))

    def testSectionFlagFallbacks(self):
        self.assertTrue(self.config.sectionFlag("plain", "missing", True))
        self.assertFalse(self.config.sectionFlag("missing", "missing"))
        self.assertTrue(self.config.sectionFlag("nested", "bare", True))


class CoreSettingTests(unittest.TestCase):

    def testTtlParsing(self):
        cases = [("2.5", 2.5), (-3, 0.0), ("abc", 5.0), (None, 5.0), (0, 0.0)]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(makeConfig({"cache_ttl_seconds": raw}).ttlSeconds, expected)

    def testEmptyEditorFallsBackToCode(self):
        self.assertEqual(makeConfig({"editor_command": ""}).editorCommand, "code")

    def testTerminalDefaultsToNone(self):
        self.assertIsNone(makeConfig({}).terminalCommand)


class ConfigPathTests(unittest.TestCase):

    def testEnvironmentOverride(self):
        with mock.patch.dict(os.environ, {"NEMO_REPO_CORE_CONFIG": "~/custom.json"}):
            self.assertEqual(defaultConfigPath(), os.path.expanduser("~/custom.json"))

    def testXdgConfigHome(self):
        environment = {"XDG_CONFIG_HOME": "/xdg/config", "NEMO_REPO_CORE_CONFIG": ""}
        with mock.patch.dict(os.environ, environment):
            self.assertEqual(defaultConfigPath(), "/xdg/config/nemo-repo-core.json")

    def testSharedConfigUsesTestPath(self):
        self.assertEqual(coreConfig.path, support.configPath)


class LogLevelTests(unittest.TestCase):

    def tearDown(self):
        applyLogLevel("critical")

    def testConfiguredLevelApplies(self):
        with mock.patch.dict(os.environ, {"NEMO_REPO_LOG": ""}):
            applyLogLevel("debug")
            self.assertEqual(_rootLogger.level, logging.DEBUG)
            applyLogLevel("unknown")
            self.assertEqual(_rootLogger.level, logging.WARNING)

    def testEnvironmentWins(self):
        with mock.patch.dict(os.environ, {"NEMO_REPO_LOG": "error"}):
            applyLogLevel("debug")
            self.assertEqual(_rootLogger.level, logging.ERROR)

    def testConfigFileLevelIsApplied(self):
        with mock.patch.dict(os.environ, {"NEMO_REPO_LOG": ""}):
            makeConfig({"log_level": "info"})
            self.assertEqual(_rootLogger.level, logging.INFO)


if __name__ == "__main__":
    unittest.main()
