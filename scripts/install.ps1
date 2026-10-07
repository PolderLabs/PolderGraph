$ErrorActionPreference = 'Stop'

$repo = 'https://github.com/PolderLabs/PolderGraph.git'

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git is required to install PolderGraph from GitHub. Install Git for Windows and retry.'
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

Write-Host 'Installing PolderGraph...'
uv tool install "poldergraph[all] @ git+$repo"
if ($LASTEXITCODE -ne 0) {
    throw "PolderGraph installation failed (uv exit code $LASTEXITCODE)."
}

Write-Host 'PolderGraph is installed. Open a new PowerShell window if the poldergraph command is not on PATH.'
Write-Host 'Run "poldergraph init" from the repository you want to index.'
