param(
    [Parameter(Mandatory = $true)]
    [string]$Installer,

    [Parameter(Mandatory = $true)]
    [string]$Signature,

    [Parameter(Mandatory = $true)]
    [string]$PublicKey,

    [Parameter(Mandatory = $true)]
    [string]$Version,

    [Parameter(Mandatory = $true)]
    [string]$Output
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$desktopRoot = Join-Path $repoRoot "apps/desktop"
$tauriRoot = Join-Path $desktopRoot "src-tauri"
$testRoot = Join-Path $env:RUNNER_TEMP "divan-production-updater-verify-$PID"
$feedRoot = Join-Path $testRoot "feed"
$stateRoot = Join-Path $testRoot "state"
$configPath = Join-Path $testRoot "tauri.production-updater-verify.json"
$markerPath = Join-Path $testRoot "marker.txt"
$server = $null

function Get-FreePort {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    try {
        return ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
    }
    finally {
        $listener.Stop()
    }
}

function Read-Marker {
    param([string]$Path)

    $values = @{}
    foreach ($line in Get-Content $Path) {
        $parts = $line -split "=", 2
        if ($parts.Count -eq 2) {
            $values[$parts[0]] = $parts[1]
        }
    }
    return $values
}

function Wait-Marker {
    param(
        [string]$Path,
        [System.Diagnostics.Process]$Process,
        [int]$TimeoutSeconds = 120
    )

    foreach ($attempt in 1..$TimeoutSeconds) {
        if (Test-Path $Path -PathType Leaf) {
            return Read-Marker -Path $Path
        }
        if ($Process.HasExited) {
            throw "production updater verifier exited without a result marker (exit $($Process.ExitCode))"
        }
        Start-Sleep -Seconds 1
    }
    throw "production updater verifier timed out after $TimeoutSeconds seconds"
}

function Get-ReleaseExecutable {
    $exact = Join-Path $tauriRoot "target/release/Ottoman.exe"
    if (Test-Path $exact -PathType Leaf) {
        return $exact
    }

    $candidates = @(
        Get-ChildItem (Join-Path $tauriRoot "target/release") -Filter "*.exe" -File |
            Where-Object { $_.Name -notmatch '(?i)(setup|installer|uninstall)' }
    )
    if ($candidates.Count -ne 1) {
        throw "could not resolve the no-bundle production updater verifier executable"
    }
    return $candidates[0].FullName
}

$installerPath = (Resolve-Path $Installer).Path
$signaturePath = (Resolve-Path $Signature).Path
$outputPath = [System.IO.Path]::GetFullPath($Output)
$cleanPublicKey = $PublicKey.Trim()
$cleanVersion = $Version.Trim()

if (-not (Test-Path $installerPath -PathType Leaf)) {
    throw "production updater installer does not exist"
}
if (-not (Test-Path $signaturePath -PathType Leaf)) {
    throw "production updater signature does not exist"
}
if ((Get-Item $installerPath).Length -le 0) {
    throw "production updater installer is empty"
}
if (-not (Get-Content $signaturePath -Raw).Trim()) {
    throw "production updater signature is empty"
}
if (-not $cleanPublicKey) {
    throw "production updater public key is empty"
}
if ($cleanVersion -notmatch '^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$') {
    throw "production updater version is not SemVer-compatible"
}

New-Item -ItemType Directory -Path $feedRoot, $stateRoot -Force | Out-Null
$servedInstaller = Join-Path $feedRoot (Split-Path -Leaf $installerPath)
Copy-Item $installerPath $servedInstaller -Force
$signatureText = (Get-Content $signaturePath -Raw).Trim()
$port = Get-FreePort

$config = [ordered]@{
    version = $cleanVersion
    bundle = [ordered]@{
        externalBin = @("binaries/divan-core")
        createUpdaterArtifacts = $false
    }
    plugins = [ordered]@{
        updater = [ordered]@{
            pubkey = $cleanPublicKey
            endpoints = @("http://127.0.0.1:$port/latest.json")
            dangerousInsecureTransportProtocol = $true
        }
    }
}
$config | ConvertTo-Json -Depth 20 | Set-Content -Path $configPath -Encoding utf8

$feed = [ordered]@{
    version = $cleanVersion
    notes = "Ottoman production updater key-pair verification"
    pub_date = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    platforms = [ordered]@{
        "windows-x86_64" = [ordered]@{
            signature = $signatureText
            url = "http://127.0.0.1:$port/$(Split-Path -Leaf $servedInstaller)"
        }
    }
}
$feed | ConvertTo-Json -Depth 20 | Set-Content -Path (Join-Path $feedRoot "latest.json") -Encoding utf8

$previousMode = $env:DIVAN_UPDATER_E2E_MODE
$previousExpected = $env:DIVAN_UPDATER_E2E_EXPECTED_VERSION
$previousMarker = $env:DIVAN_UPDATER_E2E_MARKER
$previousDataDir = $env:DIVAN_DATA_DIR

try {
    Push-Location $desktopRoot
    try {
        & pnpm tauri build --no-bundle --features updater-e2e --config $configPath
        if ($LASTEXITCODE -ne 0) {
            throw "could not build the production updater verifier"
        }
    }
    finally {
        Pop-Location
    }

    $server = Start-Process -FilePath "python" -ArgumentList @("-m", "http.server", "$port", "--bind", "127.0.0.1") -WorkingDirectory $feedRoot -PassThru -WindowStyle Hidden
    $ready = $false
    foreach ($attempt in 1..30) {
        try {
            Invoke-WebRequest -Uri "http://127.0.0.1:$port/latest.json" -UseBasicParsing -TimeoutSec 2 | Out-Null
            $ready = $true
            break
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }
    if (-not $ready) {
        throw "production updater verifier feed did not become ready"
    }

    Remove-Item $markerPath -Force -ErrorAction SilentlyContinue
    $env:DIVAN_UPDATER_E2E_MODE = "verify-download"
    $env:DIVAN_UPDATER_E2E_EXPECTED_VERSION = $cleanVersion
    $env:DIVAN_UPDATER_E2E_MARKER = $markerPath
    $env:DIVAN_DATA_DIR = $stateRoot

    $verifierExe = Get-ReleaseExecutable
    $process = Start-Process -FilePath $verifierExe -PassThru
    $marker = Wait-Marker -Path $markerPath -Process $process
    if ($marker["status"] -ne "pass" -or $marker["mode"] -ne "verify-download") {
        throw "production updater runtime verification failed: $($marker['detail'])"
    }
    if ($marker["expected"] -ne $cleanVersion) {
        throw "production updater runtime verifier reported the wrong expected version"
    }

    $sourceCommit = (& git -C $repoRoot rev-parse HEAD).Trim()
    $sourceTree = (& git -C $repoRoot rev-parse 'HEAD^{tree}').Trim()
    if ($sourceCommit -notmatch '^[0-9a-f]{40}$' -or $sourceTree -notmatch '^[0-9a-f]{40}$') {
        throw "production updater verifier could not resolve source identity"
    }

    $evidence = [ordered]@{
        schema_version = 1
        product = "Ottoman"
        status = "pass"
        verification = "tauri-runtime-download-signature"
        version = $cleanVersion
        source_commit = $sourceCommit
        source_tree = $sourceTree
        installer_sha256 = (Get-FileHash $installerPath -Algorithm SHA256).Hash.ToLowerInvariant()
        updater_signature_sha256 = (Get-FileHash $signaturePath -Algorithm SHA256).Hash.ToLowerInvariant()
        production_public_key_runtime_verified = $true
        install_performed = $false
        test_only_insecure_transport = $true
        production_transport_policy = "https-only"
    }
    $outputDirectory = Split-Path -Parent $outputPath
    if ($outputDirectory) {
        New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
    }
    $evidence | ConvertTo-Json -Depth 10 | Set-Content -Path $outputPath -Encoding utf8
}
finally {
    if ($server -and -not $server.HasExited) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    }
    $env:DIVAN_UPDATER_E2E_MODE = $previousMode
    $env:DIVAN_UPDATER_E2E_EXPECTED_VERSION = $previousExpected
    $env:DIVAN_UPDATER_E2E_MARKER = $previousMarker
    $env:DIVAN_DATA_DIR = $previousDataDir
}
