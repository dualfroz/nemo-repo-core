"""Version of the core library and the compatibility check plugins call."""

coreVersion = "1.0.0"


class CoreVersionError(RuntimeError):
    """Raised when the installed core cannot satisfy a plugin's requirement."""


def parseVersion(text):
    """Turn "1.2.3" into (1, 2, 3). Missing components count as zero."""
    parts = []
    for chunk in str(text).split("."):
        digits = "".join(character for character in chunk if character.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def satisfies(installed, minimum):
    """True when `installed` can serve a plugin that asked for `minimum`.

    The rule is plain semantic versioning: the major component must match
    exactly, and the rest must be greater than or equal to the requirement.
    """
    installedParts = parseVersion(installed)
    minimumParts = parseVersion(minimum)
    if installedParts[0] != minimumParts[0]:
        return False
    return installedParts >= minimumParts


def requireCore(minimumVersion):
    """Assert that this core is new enough for the calling plugin.

    Call it once, at import time, before touching any other core symbol.
    Nemo logs the resulting exception and skips the extension, which is the
    behaviour we want: a plugin built against a newer core must not load
    half-working.
    """
    if not satisfies(coreVersion, minimumVersion):
        raise CoreVersionError(
            "nemo-repo-core %s cannot satisfy the required version %s; "
            "update the core library" % (coreVersion, minimumVersion)
        )
    return coreVersion
