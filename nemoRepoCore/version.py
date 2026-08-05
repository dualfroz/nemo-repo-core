"""Version of the core library and the compatibility check plugins call."""

coreVersion = "0.1.0"


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


def breakingSeries(parts):
    """The leading components that have to match exactly for compatibility.

    From 1.0.0 on that is the major component alone. While the major is 0 the
    API is still allowed to change with every minor bump, so 0.1 and 0.2 are
    treated as different series and neither can serve the other.
    """
    return parts[:2] if parts[0] == 0 else parts[:1]


def satisfies(installed, minimum):
    """True when `installed` can serve a plugin that asked for `minimum`.

    Semantic versioning: the breaking component must match exactly and the
    version as a whole must be greater than or equal to the requirement.
    """
    installedParts = parseVersion(installed)
    minimumParts = parseVersion(minimum)
    if breakingSeries(installedParts) != breakingSeries(minimumParts):
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
            "install a core compatible with %s" % (coreVersion, minimumVersion, minimumVersion)
        )
    return coreVersion
