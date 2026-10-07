#!/bin/sh
set -eu

repo='https://github.com/PolderLabs/PolderGraph.git'

if ! command -v curl >/dev/null 2>&1; then
    echo 'Error: curl is required to install uv.' >&2
    exit 1
fi
if ! command -v git >/dev/null 2>&1; then
    echo 'Error: Git is required to install PolderGraph from GitHub.' >&2
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

echo 'Installing PolderGraph...'
uv tool install "poldergraph[all] @ git+$repo"
echo 'PolderGraph is installed. Open a new shell if the poldergraph command is not on PATH.'
echo 'Run "poldergraph init" from the repository you want to index.'
