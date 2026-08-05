"""Turning the Nemo.FileInfo objects handed to a provider into local paths.

Every provider needs the same two guards before it can do anything useful:
the item must live on the local filesystem, and for repository work it must
be a directory. Getting either wrong means running git against a path that
does not exist, or against an ftp:// URI.
"""

from gi.repository import GLib


def localPath(nemoFile):
    """Filesystem path for `nemoFile`, or None if it is not a local file."""
    if nemoFile.get_uri_scheme() != "file":
        return None
    try:
        return GLib.filename_from_uri(nemoFile.get_uri())[0]
    except GLib.Error:
        return None


def localDirectoryPath(nemoFile):
    """Filesystem path for `nemoFile` when it is a local directory, else None."""
    if not nemoFile.is_directory():
        return None
    return localPath(nemoFile)


def singleLocalDirectory(files):
    """Path of the one selected local directory, or None for any other case.

    Property pages and single-target menu items all want exactly this.
    """
    if len(files) != 1:
        return None
    return localDirectoryPath(files[0])
