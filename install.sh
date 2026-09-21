#!/usr/bin/env bash
set -euo pipefail

sourceDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dataHome="${XDG_DATA_HOME:-$HOME/.local/share}"
installDir="$dataHome/nemo-repo-core"

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

echo
echo "Core installed. It does nothing on its own: install at least one plugin."
