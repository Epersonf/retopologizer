#!/bin/bash
# Runs Python in the user's Chrome through browser-harness (reads the code from stdin). Usage: tools/general/bh.sh <<'PY' ... PY
# Needs: BH_REPO (default C:/Users/epers/Documents/Repositories/OpenSource/browser-harness) with its .venv, and Chrome with
# chrome://inspect/#remote-debugging allowed (the first call shows "Allow remote debugging?" in Chrome: ask the user to click Allow).
# WHY a script: under Git Bash, "$PWD" paths are converted to C:\Program Files\Git\... and the runtime dir fails with PermissionError;
# PowerShell pipes add a BOM that breaks the code (SyntaxError U+FEFF). Windows-style paths in env vars + bash stdin avoid both.
REPO="${BH_REPO:-C:/Users/epers/Documents/Repositories/OpenSource/browser-harness}"
W=$(cygpath -w "$REPO")
export BH_HOME="$W\.browser-harness-dev" BH_RUNTIME_DIR="$W\.browser-harness-dev\runtime" BH_TMP_DIR="$W\.browser-harness-dev\tmp"
cd "$REPO" && exec ./.venv/Scripts/python -m browser_harness.run "$@"
