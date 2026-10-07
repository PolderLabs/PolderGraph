$ErrorActionPreference = 'Stop'

$repo = 'PolderLabs/PolderGraph'
$releaseApi = "https://api.github.com/repos/$repo/releases/latest"

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
$wheel = $release.assets | Where-Object { $_.name -match '^poldergraph-.*\.whl$' } | Select-Object -First 1
if (-not $wheel) {
    throw "No wheel asset was found in the latest GitHub release for $repo."
}

Write-Host "Installing PolderGraph from the latest GitHub release: $($wheel.browser_download_url)"
uv tool install "poldergraph[all] @ $($wheel.browser_download_url)"
if ($LASTEXITCODE -ne 0) {
    throw "PolderGraph installation failed (uv exit code $LASTEXITCODE)."
}

Write-Host 'PolderGraph is installed. Open a new PowerShell window if the poldergraph command is not on PATH.'
Write-Host 'Run "poldergraph init" from the repository you want to index.'
