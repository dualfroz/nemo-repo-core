#!/usr/bin/env bash
set -euo pipefail

dataHome="${XDG_DATA_HOME:-$HOME/.local/share}"
installDir="$dataHome/nemo-repo-core"
extensionsDir="$dataHome/nemo-python/extensions"

if [ -e "$installDir/nemoRepoCore" ] || [ -L "$installDir/nemoRepoCore" ]; then
  rm -rf "$installDir/nemoRepoCore"
  echo "Removed $installDir/nemoRepoCore"
else
  echo "Nothing installed at $installDir/nemoRepoCore"
fi

rmdir "$installDir" 2>/dev/null || true

remaining="$(find "$extensionsDir" -maxdepth 1 \( -name 'nemoRepo*.py' -o -name 'nemoFolderTools.py' \) 2>/dev/null || true)"
if [ -n "$remaining" ]; then
  echo
  echo "WARNING: these plugins still expect the core and will now fail to load:"
  echo "$remaining"
  echo "Uninstall them too, then restart Nemo with: nemo -q"
fi
