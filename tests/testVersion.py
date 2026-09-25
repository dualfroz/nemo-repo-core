import unittest

import support

from nemoRepoCore import CoreVersionError, coreVersion, requireCore
from nemoRepoCore.version import breakingSeries, parseVersion, satisfies


class ParseVersionTests(unittest.TestCase):

    def testFullVersion(self):
        self.assertEqual(parseVersion("1.2.3"), (1, 2, 3))

    def testMissingComponentsAreZero(self):
        self.assertEqual(parseVersion("2"), (2, 0, 0))
        self.assertEqual(parseVersion("2.5"), (2, 5, 0))

    def testExtraComponentsAreIgnored(self):
        self.assertEqual(parseVersion("1.2.3.4"), (1, 2, 3))

    def testNonDigitSuffixesAreDropped(self):
        self.assertEqual(parseVersion("v1.x.2"), (1, 0, 2))


class SatisfiesTests(unittest.TestCase):

    def testBreakingSeriesWhileMajorIsZero(self):
        self.assertEqual(breakingSeries((0, 3, 1)), (0, 3))

    def testBreakingSeriesFromOneOn(self):
        self.assertEqual(breakingSeries((2, 3, 1)), (2,))

    def testSameVersion(self):
        self.assertTrue(satisfies("0.1.0", "0.1.0"))

    def testNewerPatchInZeroSeries(self):
        self.assertTrue(satisfies("0.1.4", "0.1.0"))

    def testOlderPatchInZeroSeries(self):
        self.assertFalse(satisfies("0.1.0", "0.1.2"))

    def testDifferentMinorInZeroSeries(self):
        self.assertFalse(satisfies("0.2.0", "0.1.0"))
        self.assertFalse(satisfies("0.1.0", "0.2.0"))

    def testNewerMinorInStableSeries(self):
        self.assertTrue(satisfies("1.4.0", "1.0.0"))

    def testOlderMinorInStableSeries(self):
        self.assertFalse(satisfies("1.0.0", "1.2.0"))

    def testDifferentMajor(self):
        self.assertFalse(satisfies("2.0.0", "1.0.0"))
        self.assertFalse(satisfies("1.0.0", "0.9.0"))


class RequireCoreTests(unittest.TestCase):

    def testCompatibleRequirementReturnsVersion(self):
        self.assertEqual(requireCore(coreVersion), coreVersion)

    def testIncompatibleRequirementRaises(self):
        with self.assertRaises(CoreVersionError) as raised:
            requireCore("99.0.0")
        self.assertIn("99.0.0", str(raised.exception))

    def testErrorIsRuntimeError(self):
        self.assertTrue(issubclass(CoreVersionError, RuntimeError))


if __name__ == "__main__":
    unittest.main()
