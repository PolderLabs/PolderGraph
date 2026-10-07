#!/bin/sh
set -eu

repo='PolderLabs/PolderGraph'
api="https://api.github.com/repos/$repo/releases/latest"

if ! command -v curl >/dev/null 2>&1; then
    echo 'Error: curl is required to look up the latest release.' >&2
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
tag=$(printf '%s' "$release_json" | sed -nE 's/.*"tag_name": *"([^"]+)".*/\1/p' | head -n 1)
if [ -z "$tag" ]; then
    echo "Error: the latest GitHub release for $repo has no tag." >&2
    exit 1
fi

echo "Installing PolderGraph from GitHub release $tag..."
install_dir=$(mktemp -d)
trap 'rm -rf "$install_dir"' EXIT HUP INT TERM
curl -fsSL -H 'Accept: application/vnd.github+json' \
    "https://api.github.com/repos/$repo/tarball/$tag" -o "$install_dir/source.tar.gz"
tar -xzf "$install_dir/source.tar.gz" -C "$install_dir"
source_dir=$(find "$install_dir" -mindepth 1 -maxdepth 1 -type d | head -n 1)
if [ -z "$source_dir" ] || [ ! -f "$source_dir/pyproject.toml" ]; then
    echo 'Error: failed to extract the PolderGraph release source archive.' >&2
    exit 1
fi
uv tool install --force --upgrade "poldergraph[all] @ file://$source_dir"
echo 'PolderGraph is installed. Open a new shell if the poldergraph command is not on PATH.'
echo 'Run "poldergraph init" from the repository you want to index.'
