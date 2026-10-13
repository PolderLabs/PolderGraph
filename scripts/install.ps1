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

if (-not (Get-Command curl.exe -ErrorAction SilentlyContinue)) {
    throw 'curl.exe is required to download the release archive.'
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw 'uv was installed but could not be found. Add %USERPROFILE%\.local\bin to PATH and retry.'
}

$headers = @{ Accept = 'application/vnd.github+json' }
$release = Invoke-RestMethod -Headers $headers $releaseApi
if (-not $release.tag_name) {
    throw "The latest GitHub release for $repo has no tag."
}

Write-Host "Installing PolderGraph from GitHub release $($release.tag_name)..."
Write-Host ''
Write-Host 'NOTE: PolderGraph downloads a ~2 GB embedding model the first time you run'
Write-Host '      poldergraph init. Python dependencies add another ~1.5 GB.'
Write-Host '      Expect 3-4 GB of free disk space.'
Write-Host ''
$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $tempDir | Out-Null
try {
    # Prefer the wheel published with the release. It already contains the built
    # dashboard, so installing it needs neither Node.js nor a source build. Only
    # fall back to the source archive if no wheel is attached.
    $version = $release.tag_name -replace '^v', ''
    $wheelName = "poldergraph-$version-py3-none-any.whl"
    $wheel = Join-Path $tempDir $wheelName
    $wheelUrl = "https://github.com/$repo/releases/download/$($release.tag_name)/$wheelName"

    & curl.exe --fail --silent --show-error --location --output $wheel $wheelUrl
    if ($LASTEXITCODE -eq 0 -and (Test-Path $wheel)) {
        Write-Host "Installing the published wheel for $($release.tag_name)..."
        # A bare Windows path is not a valid reference for uv; make it a file:// URI.
        $wheelUri = ([System.Uri]$wheel).AbsoluteUri
        uv tool install --force --upgrade "poldergraph[all] @ $wheelUri"
    }
    else {
        Write-Host "No wheel found for $($release.tag_name); building from the source archive."
        $archive = Join-Path $tempDir 'source.tar.gz'
        $archiveUrl = "https://api.github.com/repos/$repo/tarball/$($release.tag_name)"
        & curl.exe --fail --silent --show-error --location `
            --header 'Accept: application/vnd.github+json' `
            --output $archive $archiveUrl
        if ($LASTEXITCODE -ne 0) {
            throw "Could not download the PolderGraph release archive (curl exit code $LASTEXITCODE)."
        }
        tar -xzf $archive -C $tempDir
        if ($LASTEXITCODE -ne 0) {
            throw 'Could not extract the PolderGraph release source archive.'
        }

        $sourceDir = Get-ChildItem -Path $tempDir -Directory | Select-Object -First 1
        if (-not $sourceDir -or -not (Test-Path (Join-Path $sourceDir.FullName 'pyproject.toml'))) {
            throw 'Could not find the PolderGraph project in the release source archive.'
        }

        $sourceUri = ([System.Uri]$sourceDir.FullName).AbsoluteUri
        uv tool install --force --upgrade "poldergraph[all] @ $sourceUri"
    }
    if ($LASTEXITCODE -ne 0) {
        throw "PolderGraph installation failed (uv exit code $LASTEXITCODE)."
    }
}
finally {
    Remove-Item -LiteralPath $tempDir -Recurse -Force
}

Write-Host 'PolderGraph is installed. Open a new PowerShell window if the poldergraph command is not on PATH.'
Write-Host 'Run "poldergraph init" from the repository you want to index.'
