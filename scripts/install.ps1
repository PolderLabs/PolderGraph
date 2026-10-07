$ErrorActionPreference = 'Stop'

$repo = 'PolderLabs/PolderGraph'
$releaseApi = "https://api.github.com/repos/$repo/releases/latest"
$source = "https://github.com/$repo.git"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git is required to install PolderGraph from the release source. Install Git for Windows and retry.'
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host 'Installing uv...'
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression

    $uvInstallDir = Join-Path $env:USERPROFILE '.local\bin'
    if (Test-Path (Join-Path $uvInstallDir 'uv.exe')) {
        $env:Path = "$uvInstallDir;$env:Path"
    }
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw 'uv was installed but could not be found. Add %USERPROFILE%\.local\bin to PATH and retry.'
}

$release = Invoke-RestMethod -Headers @{ Accept = 'application/vnd.github+json' } $releaseApi
if (-not $release.tag_name) {
    throw "The latest GitHub release for $repo has no tag."
}

Write-Host "Installing PolderGraph from GitHub release $($release.tag_name)..."
uv tool install --upgrade --from "git+$source@$($release.tag_name)" 'poldergraph[all]'
if ($LASTEXITCODE -ne 0) {
    throw "PolderGraph installation failed (uv exit code $LASTEXITCODE)."
}

Write-Host 'PolderGraph is installed. Open a new PowerShell window if the poldergraph command is not on PATH.'
Write-Host 'Run "poldergraph init" from the repository you want to index.'
