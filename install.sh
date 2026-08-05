#!/usr/bin/env bash
# Installs the nemoRepoCore library for the current user. No root needed.
#
#   ./install.sh          link the package (edits in this checkout go live)
#   ./install.sh --copy   copy the package instead of linking it
#
# The package is placed in a version independent directory under
# XDG_DATA_HOME, so a Python upgrade cannot orphan it. Plugins locate it from
# there; see "Writing a plugin" in README.md.
set -euo pipefail

sourceDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dataHome="${XDG_DATA_HOME:-$HOME/.local/share}"
installDir="$dataHome/nemo-repo-core"
configDir="${XDG_CONFIG_HOME:-$HOME/.config}"
extensionsDir="$dataHome/nemo-python/extensions"

mode="link"
if [ "${1:-}" = "--copy" ]; then
  mode="copy"
elif [ -n "${1:-}" ]; then
  echo "usage: $0 [--copy]" >&2
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found in PATH" >&2
  exit 1
fi

mkdir -p "$installDir"
rm -rf "$installDir/nemoRepoCore"

if [ "$mode" = "copy" ]; then
  cp -r "$sourceDir/nemoRepoCore" "$installDir/nemoRepoCore"
  echo "Copied nemoRepoCore -> $installDir/nemoRepoCore"
else
  ln -s "$sourceDir/nemoRepoCore" "$installDir/nemoRepoCore"
  echo "Linked nemoRepoCore -> $installDir/nemoRepoCore"
fi

if ! PYTHONPATH="$installDir" python3 -c "import nemoRepoCore" 2>/dev/null; then
  echo
  echo "WARNING: the package was installed but could not be imported."
  echo "Check that python3-gi and gir1.2-nemo-3.0 are installed:"
  echo "  sudo apt install python3-gi gir1.2-nemo-3.0 python-nemo"
  exit 1
fi

coreVersion="$(PYTHONPATH="$installDir" python3 -c 'import nemoRepoCore; print(nemoRepoCore.coreVersion)')"
echo "Import check passed, core version $coreVersion"

legacyConfig="$configDir/nemo-repo-emblems.json"
newConfig="$configDir/nemo-repo-core.json"
if [ -f "$legacyConfig" ] && [ ! -f "$newConfig" ]; then
  echo
  echo "Found a config from the pre-split extension:"
  echo "  $legacyConfig"
  echo "It will be copied to $newConfig the first time a plugin loads."
  echo "The old file is left untouched."
fi

legacyExtension="$extensionsDir/nemo_repo_emblems.py"
if [ -e "$legacyExtension" ]; then
  echo
  echo "WARNING: the pre-split single file extension is still installed:"
  echo "  $legacyExtension"
  echo "Running it alongside the new plugins duplicates emblems, columns and"
  echo "menu entries. Remove it when you are ready to switch over:"
  echo "  rm \"$legacyExtension\""
fi

echo
echo "Core installed. It does nothing on its own: install at least one plugin."
