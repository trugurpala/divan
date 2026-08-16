param(
    [Parameter(Mandatory = $true)]
    [string]$Output
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$desktopRoot = Join-Path $repoRoot "apps/desktop"
$tauriRoot = Join-Path $desktopRoot "src-tauri"
$baseConfigPath = Join-Path $tauriRoot "tauri.conf.json"
$testRoot = Join-Path $env:RUNNER_TEMP "divan-updater-e2e-$PID"
$keyRoot = Join-Path $testRoot "keys"
$artifactRoot = Join-Path $testRoot "artifacts"
$feedRoot = Join-Path $testRoot "feed"
$stateRoot = Join-Path $testRoot "state"
New-Item -ItemType Directory -Path $keyRoot, $artifactRoot, $feedRoot, $stateRoot -Force | Out-Null

$privateKeyPath = Join-Path $keyRoot "updater.key"
$keyPassword = "divan-ci-updater-e2e"
$server = $null
$installedApp = Join-Path $env:LOCALAPPDATA "Ottoman/Ottoman.exe"

function Set-ExactWorkflowSource {
    $eventPath = $env:GITHUB_EVENT_PATH
    if (-not $eventPath -or -not (Test-Path $eventPath -PathType Leaf)) {
        return
    }

    $eventPayload = Get-Content $eventPath -Raw | ConvertFrom-Json
    $pullRequestProperty = $eventPayload.PSObject.Properties["pull_request"]
    if ($null -eq $pullRequestProperty) {
        return
    }
    $headProperty = $pullRequestProperty.Value.PSObject.Properties["head"]
    if ($null -eq $headProperty) {
        throw "pull_request event is missing head metadata"
    }
    $shaProperty = $headProperty.Value.PSObject.Properties["sha"]
    if ($null -eq $shaProperty) {
        throw "pull_request event is missing head SHA"
    }
    $headSha = [string]$shaProperty.Value
    if ($headSha -notmatch '^[0-9a-f]{40}$') {
        throw "pull_request head SHA is invalid"
    }

    $current = (& git -C $repoRoot rev-parse HEAD).Trim()
    if ($current -eq $headSha) {
        return
    }

    & git -C $repoRoot fetch --no-tags --depth=1 origin $headSha
    if ($LASTEXITCODE -ne 0) {
        throw "Could not fetch exact pull request head SHA $headSha"
    }
    & git -C $repoRoot checkout --force $headSha
    if ($LASTEXITCODE -ne 0) {
        throw "Could not checkout exact pull request head SHA $headSha"
    }
    $resolved = (& git -C $repoRoot rev-parse HEAD).Trim()
    if ($resolved -ne $headSha) {
        throw "Updater e2e checkout did not resolve to exact pull request head"
    }
}

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

function Write-TestConfig {
    param(
        [string]$Version,
        [string]$PublicKey,
        [int]$Port
    )

    $configPath = Join-Path $testRoot "tauri-updater-$($Version.Replace('.', '-')).json"
    $config = [ordered]@{
        version = $Version
        bundle = [ordered]@{
            externalBin = @("binaries/divan-core")
            createUpdaterArtifacts = $true
        }
        plugins = [ordered]@{
            updater = [ordered]@{
                pubkey = $PublicKey
                endpoints = @("http://127.0.0.1:$Port/latest.json")
                dangerousInsecureTransportProtocol = $true
            }
        }
    }
    $config | ConvertTo-Json -Depth 20 | Set-Content -Path $configPath -Encoding utf8
    return $configPath
}

function Build-TestVersion {
    param(
        [string]$Version,
        [string]$PublicKey,
        [int]$Port
    )

    $configPath = Write-TestConfig -Version $Version -PublicKey $PublicKey -Port $Port
    $bundleRoot = Join-Path $tauriRoot "target/release/bundle/nsis"
    if (Test-Path $bundleRoot) {
        Remove-Item $bundleRoot -Recurse -Force
    }

    Push-Location $desktopRoot
    try {
        & pnpm tauri build --bundles nsis --features updater-e2e --config $configPath | Out-Host
        if ($LASTEXITCODE -ne 0) {
            throw "Tauri updater e2e build failed for version $Version"
        }
    }
    finally {
        Pop-Location
    }

    $installer = Get-ChildItem $bundleRoot -Filter "*-setup.exe" -File | Select-Object -First 1
    if (-not $installer) {
        throw "Updater e2e installer was not produced for version $Version"
    }
    $signaturePath = "$($installer.FullName).sig"
    if (-not (Test-Path $signaturePath -PathType Leaf)) {
        throw "Updater e2e signature was not produced for version $Version"
    }
    if (-not (Get-Content $signaturePath -Raw).Trim()) {
        throw "Updater e2e signature is empty for version $Version"
    }

    $destination = Join-Path $artifactRoot $Version
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    $installerCopy = Join-Path $destination $installer.Name
    $signatureCopy = "$installerCopy.sig"
    Copy-Item $installer.FullName $installerCopy -Force
    Copy-Item $signaturePath $signatureCopy -Force
    return [pscustomobject]@{
        Version = $Version
        Installer = $installerCopy
        Signature = $signatureCopy
        Sha256 = (Get-FileHash $installerCopy -Algorithm SHA256).Hash.ToLowerInvariant()
        SignatureSha256 = (Get-FileHash $signatureCopy -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

function Set-TestFeed {
    param(
        [object]$Artifact,
        [int]$Port,
        [switch]$TamperSignature
    )

    $installerName = Split-Path -Leaf $Artifact.Installer
    $servedInstaller = Join-Path $feedRoot $installerName
    Copy-Item $Artifact.Installer $servedInstaller -Force
    $signature = (Get-Content $Artifact.Signature -Raw).Trim()
    if ($TamperSignature) {
        $signature = "X$signature"
    }
    $feed = [ordered]@{
        version = $Artifact.Version
        notes = "Ottoman updater runtime e2e"
        pub_date = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
        platforms = [ordered]@{
            "windows-x86_64" = [ordered]@{
                signature = $signature
                url = "http://127.0.0.1:$Port/$installerName"
            }
        }
    }
    $feed | ConvertTo-Json -Depth 20 | Set-Content -Path (Join-Path $feedRoot "latest.json") -Encoding utf8
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
        [int]$TimeoutSeconds = 90,
        [switch]$AllowExitWithoutMarker
    )

    foreach ($attempt in 1..$TimeoutSeconds) {
        if (Test-Path $Path -PathType Leaf) {
            $marker = Read-Marker -Path $Path
            if ($marker["status"] -eq "pass") {
                return $marker
            }
            throw "Updater e2e probe failed: $($marker['detail'])"
        }
        if ($Process.HasExited) {
            if ($AllowExitWithoutMarker) {
                return $null
            }
            throw "Updater e2e app exited without a result marker (exit $($Process.ExitCode))"
        }
        Start-Sleep -Seconds 1
    }
    throw "Updater e2e marker timed out after $TimeoutSeconds seconds"
}

function Get-InstalledBinaryVersion {
    param([string]$Path)

    if (-not (Test-Path $Path -PathType Leaf)) {
        return $null
    }

    try {
        $versionInfo = (Get-Item -LiteralPath $Path -ErrorAction Stop).VersionInfo
        $rawVersion = [string]$versionInfo.ProductVersion
        if (-not $rawVersion) {
            $rawVersion = [string]$versionInfo.FileVersion
        }
        if (-not $rawVersion) {
            return $null
        }
        $match = [regex]::Match($rawVersion, '\d+\.\d+\.\d+(?:\.\d+)?')
        if (-not $match.Success) {
            return $null
        }
        return [version]$match.Value
    }
    catch {
        # NSIS can briefly replace or lock the executable. A read failure is
        # not a PASS; the bounded caller retries until the file is readable.
        return $null
    }
}

function Wait-InstalledBinaryVersion {
    param(
        [string]$Expected,
        [int]$TimeoutSeconds = 180
    )

    $expectedVersion = [version]$Expected
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        $observed = Get-InstalledBinaryVersion -Path $installedApp
        if (
            $null -ne $observed -and
            $observed.Major -eq $expectedVersion.Major -and
            $observed.Minor -eq $expectedVersion.Minor -and
            $observed.Build -eq $expectedVersion.Build
        ) {
            return $observed
        }
        Start-Sleep -Milliseconds 500
    }

    throw "Installed Ottoman binary version did not become $Expected within $TimeoutSeconds seconds"
}

function Clear-VerifiedUpdaterInstaller {
    param(
        [string]$Expected,
        [int]$GraceSeconds = 8,
        [int]$CleanupTimeoutSeconds = 10
    )

    # Installer lifetime is not release evidence. On headless hosted Windows
    # runners the passive NSIS process can outlive a completed replacement.
    # This cleanup is permitted only after both the on-disk PE version and a
    # freshly launched Tauri runtime have independently proven $Expected.
    $graceDeadline = [DateTime]::UtcNow.AddSeconds($GraceSeconds)
    while ([DateTime]::UtcNow -lt $graceDeadline) {
        $installers = @(Get-Process -Name "Ottoman-*-installer" -ErrorAction SilentlyContinue)
        if ($installers.Count -eq 0) {
            return
        }
        Start-Sleep -Milliseconds 500
    }

    $installers = @(Get-Process -Name "Ottoman-*-installer" -ErrorAction SilentlyContinue)
    foreach ($installer in $installers) {
        Stop-Process -Id $installer.Id -Force -ErrorAction SilentlyContinue
    }

    $cleanupDeadline = [DateTime]::UtcNow.AddSeconds($CleanupTimeoutSeconds)
    while ([DateTime]::UtcNow -lt $cleanupDeadline) {
        if (@(Get-Process -Name "Ottoman-*-installer" -ErrorAction SilentlyContinue).Count -eq 0) {
            return
        }
        Start-Sleep -Milliseconds 250
    }

    throw "Test-only updater installer cleanup did not complete after verified runtime $Expected"
}

function Invoke-Probe {
    param(
        [string]$Mode,
        [string]$Expected,
        [int]$TimeoutSeconds = 90
    )

    $markerPath = Join-Path $testRoot "marker-$Mode-$($Expected.Replace('.', '-')).txt"
    Remove-Item $markerPath -Force -ErrorAction SilentlyContinue
    $env:DIVAN_UPDATER_E2E_MODE = $Mode
    $env:DIVAN_UPDATER_E2E_EXPECTED_VERSION = $Expected
    $env:DIVAN_UPDATER_E2E_MARKER = $markerPath
    $process = Start-Process -FilePath $installedApp -PassThru
    return Wait-Marker -Path $markerPath -Process $process -TimeoutSeconds $TimeoutSeconds
}

function Wait-InstalledVersion {
    param(
        [string]$Expected,
        [int]$TimeoutSeconds = 120
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $attempt = 0
    while ([DateTime]::UtcNow -lt $deadline) {
        $attempt += 1
        if (-not (Test-Path $installedApp -PathType Leaf)) {
            Start-Sleep -Seconds 2
            continue
        }
        $markerPath = Join-Path $testRoot "version-$attempt.txt"
        Remove-Item $markerPath -Force -ErrorAction SilentlyContinue
        $env:DIVAN_UPDATER_E2E_MODE = "report-version"
        $env:DIVAN_UPDATER_E2E_EXPECTED_VERSION = $Expected
        $env:DIVAN_UPDATER_E2E_MARKER = $markerPath
        try {
            $process = Start-Process -FilePath $installedApp -PassThru
            foreach ($inner in 1..12) {
                if (Test-Path $markerPath -PathType Leaf) {
                    $marker = Read-Marker -Path $markerPath
                    if ($marker["status"] -eq "pass") {
                        # The Rust probe writes the marker immediately before
                        # app.exit(). Ensure this test-only process actually
                        # drains so it cannot keep the passive NSIS updater open.
                        if (-not $process.HasExited -and -not $process.WaitForExit(5000)) {
                            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
                            $null = $process.WaitForExit(5000)
                        }
                        return $marker
                    }
                    break
                }
                if ($process.HasExited) { break }
                Start-Sleep -Milliseconds 500
            }
            if (-not $process.HasExited) {
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            }
        }
        catch {
            # The NSIS updater may briefly replace/lock the executable. Retry
            # until the bounded deadline rather than treating that race as PASS.
        }
        Start-Sleep -Seconds 2
    }
    throw "Installed Ottoman version did not become $Expected within $TimeoutSeconds seconds"
}

function Invoke-SignedUpgrade {
    param([string]$Expected)

    $markerPath = Join-Path $testRoot "install-$($Expected.Replace('.', '-')).txt"
    Remove-Item $markerPath -Force -ErrorAction SilentlyContinue
    $env:DIVAN_UPDATER_E2E_MODE = "install"
    $env:DIVAN_UPDATER_E2E_EXPECTED_VERSION = $Expected
    $env:DIVAN_UPDATER_E2E_MARKER = $markerPath
    $process = Start-Process -FilePath $installedApp -PassThru
    $result = Wait-Marker -Path $markerPath -Process $process -TimeoutSeconds 180 -AllowExitWithoutMarker
    if ($null -ne $result) {
        return $result
    }

    # Tauri quits the Windows application before NSIS installation. Prove the
    # replacement from two independent product signals: first the on-disk PE
    # version, then Tauri's own runtime package version. Only after both pass do
    # we perform bounded test-runner cleanup for any passive NSIS process that
    # lingers on the headless hosted runner. Cleanup never authorizes PASS.
    Wait-InstalledBinaryVersion -Expected $Expected -TimeoutSeconds 180 | Out-Null
    $runtimeResult = Wait-InstalledVersion -Expected $Expected -TimeoutSeconds 90
    Clear-VerifiedUpdaterInstaller -Expected $Expected
    return $runtimeResult
}

$previousPrivateKey = $env:TAURI_SIGNING_PRIVATE_KEY
$previousPassword = $env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD
$previousMode = $env:DIVAN_UPDATER_E2E_MODE
$previousExpected = $env:DIVAN_UPDATER_E2E_EXPECTED_VERSION
$previousMarker = $env:DIVAN_UPDATER_E2E_MARKER
$previousDataDir = $env:DIVAN_DATA_DIR

try {
    Set-ExactWorkflowSource
    $sourceCommit = (& git -C $repoRoot rev-parse HEAD).Trim()
    $sourceTree = (& git -C $repoRoot rev-parse 'HEAD^{tree}').Trim()
    if ($sourceCommit -notmatch '^[0-9a-f]{40}$' -or $sourceTree -notmatch '^[0-9a-f]{40}$') {
        throw "Updater e2e source identity could not be resolved"
    }

    $baseConfig = Get-Content $baseConfigPath -Raw | ConvertFrom-Json
    $baseVersion = [version]$baseConfig.version
    $versionN = "{0}.{1}.{2}" -f $baseVersion.Major, $baseVersion.Minor, $baseVersion.Build
    $versionN1 = "{0}.{1}.{2}" -f $baseVersion.Major, $baseVersion.Minor, ($baseVersion.Build + 1)
    $versionN2 = "{0}.{1}.{2}" -f $baseVersion.Major, $baseVersion.Minor, ($baseVersion.Build + 2)
    $port = Get-FreePort

    Push-Location $desktopRoot
    try {
        & pnpm install --frozen-lockfile
        if ($LASTEXITCODE -ne 0) { throw "Could not install exact-head frontend dependencies for updater e2e" }
        & pnpm build
        if ($LASTEXITCODE -ne 0) { throw "Could not build exact-head frontend for updater e2e" }
        & pnpm tauri signer generate -w $privateKeyPath -p $keyPassword --ci
        if ($LASTEXITCODE -ne 0) { throw "Could not generate ephemeral Tauri updater signing key" }
        & pnpm core:build
        if ($LASTEXITCODE -ne 0) { throw "Could not build exact Core sidecar for updater e2e" }
    }
    finally {
        Pop-Location
    }

    $publicKeyPath = "$privateKeyPath.pub"
    if (-not (Test-Path $publicKeyPath -PathType Leaf)) {
        $candidatePublicKey = Get-ChildItem $keyRoot -Filter "*.pub" -File | Select-Object -First 1
        if ($candidatePublicKey) {
            $publicKeyPath = $candidatePublicKey.FullName
        }
    }
    if (-not $publicKeyPath -or -not (Test-Path $publicKeyPath -PathType Leaf)) {
        throw "Ephemeral Tauri updater public key was not generated"
    }
    $publicKey = (Get-Content $publicKeyPath -Raw).Trim()
    if (-not $publicKey) { throw "Ephemeral Tauri updater public key is empty" }

    $env:TAURI_SIGNING_PRIVATE_KEY = Get-Content $privateKeyPath -Raw
    $env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD = $keyPassword
    $env:DIVAN_DATA_DIR = $stateRoot

    $artifactN = Build-TestVersion -Version $versionN -PublicKey $publicKey -Port $port
    $artifactN1 = Build-TestVersion -Version $versionN1 -PublicKey $publicKey -Port $port
    $artifactN2 = Build-TestVersion -Version $versionN2 -PublicKey $publicKey -Port $port

    $install = Start-Process -FilePath $artifactN.Installer -ArgumentList "/S" -Wait -PassThru
    if ($install.ExitCode -ne 0) {
        throw "Could not install updater e2e baseline $versionN"
    }
    if (-not (Test-Path $installedApp -PathType Leaf)) {
        throw "Installed Ottoman.exe was not found after baseline install"
    }
    Wait-InstalledBinaryVersion -Expected $versionN -TimeoutSeconds 30 | Out-Null
    Wait-InstalledVersion -Expected $versionN -TimeoutSeconds 45 | Out-Null

    Set-TestFeed -Artifact $artifactN1 -Port $port
    $server = Start-Process -FilePath "python" -ArgumentList @("-m", "http.server", "$port", "--bind", "127.0.0.1") -WorkingDirectory $feedRoot -PassThru -WindowStyle Hidden
    foreach ($attempt in 1..30) {
        try {
            Invoke-WebRequest -Uri "http://127.0.0.1:$port/latest.json" -UseBasicParsing -TimeoutSec 2 | Out-Null
            break
        }
        catch {
            if ($attempt -eq 30) { throw "Local updater e2e feed server did not start" }
            Start-Sleep -Milliseconds 500
        }
    }

    Invoke-SignedUpgrade -Expected $versionN1 | Out-Null
    $validUpgrade = $true

    Set-TestFeed -Artifact $artifactN2 -Port $port -TamperSignature
    Invoke-Probe -Mode "expect-install-error" -Expected $versionN2 -TimeoutSeconds 90 | Out-Null
    Wait-InstalledVersion -Expected $versionN1 -TimeoutSeconds 45 | Out-Null
    $tamperedSignatureRejected = $true

    Set-TestFeed -Artifact $artifactN2 -Port $port
    Invoke-SignedUpgrade -Expected $versionN2 | Out-Null
    $forwardRecovery = $true

    Set-TestFeed -Artifact $artifactN -Port $port
    Invoke-Probe -Mode "expect-no-update" -Expected $versionN2 -TimeoutSeconds 60 | Out-Null
    $downgradeNotOffered = $true

    $evidence = [ordered]@{
        schema_version = 1
        status = "pass"
        source_commit = $sourceCommit
        source_tree = $sourceTree
        baseline_version = $versionN
        upgraded_version = $versionN1
        recovered_version = $versionN2
        valid_signed_upgrade = $validUpgrade
        tampered_signature_rejected = $tamperedSignatureRejected
        forward_signed_recovery = $forwardRecovery
        downgrade_not_offered = $downgradeNotOffered
        signatures_mandatory = $true
        test_only_insecure_transport = $true
        production_transport_policy = "https-only"
        baseline_installer_sha256 = $artifactN.Sha256
        upgrade_installer_sha256 = $artifactN1.Sha256
        recovery_installer_sha256 = $artifactN2.Sha256
        baseline_signature_sha256 = $artifactN.SignatureSha256
        upgrade_signature_sha256 = $artifactN1.SignatureSha256
        recovery_signature_sha256 = $artifactN2.SignatureSha256
    }
    $outputParent = Split-Path -Parent $Output
    if ($outputParent) { New-Item -ItemType Directory -Path $outputParent -Force | Out-Null }
    $evidence | ConvertTo-Json -Depth 20 | Set-Content -Path $Output -Encoding utf8
    $evidence | ConvertTo-Json -Depth 20
}
finally {
    if ($server -and -not $server.HasExited) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    }
    foreach ($name in @("DIVAN_UPDATER_E2E_MODE", "DIVAN_UPDATER_E2E_EXPECTED_VERSION", "DIVAN_UPDATER_E2E_MARKER")) {
        Remove-Item "Env:$name" -ErrorAction SilentlyContinue
    }
    if (Test-Path $installedApp -PathType Leaf) {
        $installRoot = Split-Path -Parent $installedApp
        $uninstaller = Get-ChildItem $installRoot -Filter "uninstall*.exe" -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($uninstaller) {
            Start-Process -FilePath $uninstaller.FullName -ArgumentList "/S" -Wait | Out-Null
        }
    }
    if ($null -eq $previousPrivateKey) { Remove-Item Env:TAURI_SIGNING_PRIVATE_KEY -ErrorAction SilentlyContinue } else { $env:TAURI_SIGNING_PRIVATE_KEY = $previousPrivateKey }
    if ($null -eq $previousPassword) { Remove-Item Env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD -ErrorAction SilentlyContinue } else { $env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD = $previousPassword }
    if ($null -eq $previousMode) { Remove-Item Env:DIVAN_UPDATER_E2E_MODE -ErrorAction SilentlyContinue } else { $env:DIVAN_UPDATER_E2E_MODE = $previousMode }
    if ($null -eq $previousExpected) { Remove-Item Env:DIVAN_UPDATER_E2E_EXPECTED_VERSION -ErrorAction SilentlyContinue } else { $env:DIVAN_UPDATER_E2E_EXPECTED_VERSION = $previousExpected }
    if ($null -eq $previousMarker) { Remove-Item Env:DIVAN_UPDATER_E2E_MARKER -ErrorAction SilentlyContinue } else { $env:DIVAN_UPDATER_E2E_MARKER = $previousMarker }
    if ($null -eq $previousDataDir) { Remove-Item Env:DIVAN_DATA_DIR -ErrorAction SilentlyContinue } else { $env:DIVAN_DATA_DIR = $previousDataDir }
}
