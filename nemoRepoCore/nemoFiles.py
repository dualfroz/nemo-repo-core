from gi.repository import GLib


def localPath(nemoFile):
    if nemoFile.get_uri_scheme() != "file":
        return None
    try:
        return GLib.filename_from_uri(nemoFile.get_uri())[0]
    except GLib.Error:
        return None


def localDirectoryPath(nemoFile):
    if not nemoFile.is_directory():
        return None
    return localPath(nemoFile)


def singleLocalDirectory(files):
    if len(files) != 1:
        return None
    return localDirectoryPath(files[0])
