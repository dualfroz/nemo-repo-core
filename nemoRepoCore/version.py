coreVersion = "0.1.0"


class CoreVersionError(RuntimeError):
    pass


def parseVersion(text):
    parts = []
    for chunk in str(text).split("."):
        digits = "".join(character for character in chunk if character.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def breakingSeries(parts):
    return parts[:2] if parts[0] == 0 else parts[:1]


def satisfies(installed, minimum):
    installedParts = parseVersion(installed)
    minimumParts = parseVersion(minimum)
    if breakingSeries(installedParts) != breakingSeries(minimumParts):
        return False
    return installedParts >= minimumParts


def requireCore(minimumVersion):
    if not satisfies(coreVersion, minimumVersion):
        raise CoreVersionError(
            "nemo-repo-core %s cannot satisfy the required version %s; "
            "install a core compatible with %s" % (coreVersion, minimumVersion, minimumVersion)
        )
    return coreVersion
