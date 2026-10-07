#!/bin/sh
set -eu

repo='PolderLabs/PolderGraph'
api="https://api.github.com/repos/$repo/releases/latest"

if ! command -v curl >/dev/null 2>&1; then
    echo 'Error: curl is required to download the latest release.' >&2
    exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
    echo 'Installing uv...'
    curl -LsSf https://astral.sh/uv/install.sh | sh
    PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    export PATH
fi

if ! command -v uv >/dev/null 2>&1; then
    echo 'Error: uv was installed but could not be found. Add ~/.local/bin to PATH and retry.' >&2
    exit 1
fi

release_json=$(curl -fsSL -H 'Accept: application/vnd.github+json' "$api")
wheel_url=$(printf '%s' "$release_json" | sed -nE 's/.*"browser_download_url": *"([^"]+\.whl)".*/\1/p' | head -n 1)
if [ -z "$wheel_url" ]; then
    echo "Error: no wheel asset was found in the latest GitHub release for $repo." >&2
    exit 1
fi

echo "Installing PolderGraph from the latest GitHub release: $wheel_url"
uv tool install "poldergraph[all] @ $wheel_url"
echo 'PolderGraph is installed. Open a new shell if the poldergraph command is not on PATH.'
echo 'Run "poldergraph init" from the repository you want to index.'
