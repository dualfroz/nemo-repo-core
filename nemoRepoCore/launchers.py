"""Starting a terminal or an editor from a Nemo menu item.

Terminal emulators disagree about the flag that means "run this command",
so the mapping below is explicit rather than assuming one form works
everywhere. Unknown emulators fall back to -e, which is the oldest and most
widely accepted spelling.
"""

import os
import shutil
import subprocess

from gi.repository import GLib

from .Config import coreConfig
from .logs import pluginLogger

logger = pluginLogger("launchers")

terminalCandidates = [
    "gnome-terminal",
    "x-terminal-emulator",
    "tilix",
    "konsole",
    "xfce4-terminal",
    "mate-terminal",
    "kitty",
    "alacritty",
    "xterm",
]

terminalCommandFlags = {
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

fallbackCommandFlags = ["-e"]


def resolveTerminal():
    """The terminal command to use: the configured one, else the first found."""
    configured = coreConfig.terminalCommand
    if configured and shutil.which(configured.split(" ")[0]):
        return configured
    for candidate in terminalCandidates:
        if shutil.which(candidate):
            return candidate
    return None


def _commandFlagsFor(terminal):
    return terminalCommandFlags.get(os.path.basename(terminal), fallbackCommandFlags)


def launchTerminal(path, shellCommand=None):
    """Open a terminal in `path`, optionally running `shellCommand` first.

    The shell stays open afterwards so the user can read the output of
    whatever was run and keep working in the same directory.
    """
    terminal = resolveTerminal()
    if not terminal:
        logger.warning("No terminal emulator found; tried %s",
                       ", ".join(terminalCandidates))
        return False

    parts = terminal.split(" ")
    try:
        if shellCommand:
            script = "cd %s && %s; exec \"${SHELL:-bash}\"" % (
                GLib.shell_quote(path), shellCommand)
            arguments = parts + _commandFlagsFor(parts[0]) + ["bash", "-c", script]
        else:
            arguments = parts
        subprocess.Popen(arguments, cwd=path)
    except OSError as error:
        logger.warning("Could not start %s: %s", terminal, error)
        return False
    return True


def launchEditor(path):
    """Open `path` in the configured editor command."""
    editor = coreConfig.editorCommand
    parts = editor.split(" ")
    if not shutil.which(parts[0]):
        logger.warning("Editor command %r is not in PATH", editor)
        return False
    try:
        subprocess.Popen(parts + [path])
    except OSError as error:
        logger.warning("Could not start editor %r: %s", editor, error)
        return False
    return True


def editorAvailable():
    """True when the configured editor command can actually be started."""
    return shutil.which(coreConfig.editorCommand.split(" ")[0]) is not None
