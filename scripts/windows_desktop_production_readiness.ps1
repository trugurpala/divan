param(
    [Parameter(Mandatory = $true)]
    [string]$Output
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$desktopRoot = Join-Path $repoRoot "apps/desktop"
$tauriRoot = Join-Path $desktopRoot "src-tauri"
$testRoot = Join-Path $env:RUNNER_TEMP "divan-production-readiness-$PID"
$configPath = Join-Path $testRoot "tauri.production-readiness.json"
$authenticodeProbe = Join-Path $testRoot "authenticode-probe.exe"
$updaterProbe = Join-Path $testRoot "updater-signing-probe.bin"

function Require-EnvironmentValue {
    param([string]$Name)

    $value = [Environment]::GetEnvironmentVariable($Name)
    if (-not $value -or -not $value.Trim()) {
        throw "$Name is required in the production-release environment"
    }
    return $value
}

function Get-Sha256Text {
    param([string]$Value)

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
    $digest = [System.Security.Cryptography.SHA256]::HashData($bytes)
    return [Convert]::ToHexString($digest).ToLowerInvariant()
}

function Assert-HttpsUrl {
    param(
        [string]$Name,
        [string]$Value
    )

    $uri = $null
    if (-not [Uri]::TryCreate($Value, [UriKind]::Absolute, [ref]$uri)) {
        throw "$Name must be an absolute URL"
    }
    if ($uri.Scheme -ne "https") {
        throw "$Name must use HTTPS"
    }
    if (-not $uri.Host -or $uri.UserInfo) {
        throw "$Name must not contain credentials and must have a host"
    }
    return $uri
}

New-Item -ItemType Directory -Path $testRoot -Force | Out-Null

try {
    $sourceCommit = (& git -C $repoRoot rev-parse HEAD).Trim().ToLowerInvariant()
    $sourceTree = (& git -C $repoRoot rev-parse 'HEAD^{tree}').Trim().ToLowerInvariant()
    if ($sourceCommit -notmatch '^[0-9a-f]{40}$' -or $sourceTree -notmatch '^[0-9a-f]{40}$') {
        throw "Production readiness source identity could not be resolved"
    }
    if ($env:GITHUB_SHA -and $sourceCommit -ne $env:GITHUB_SHA.Trim().ToLowerInvariant()) {
        throw "Production readiness checkout is not bound to the exact workflow source commit"
    }

    $publicKey = Require-EnvironmentValue -Name "DIVAN_UPDATER_PUBKEY"
    $updaterEndpoint = Require-EnvironmentValue -Name "DIVAN_UPDATER_ENDPOINT"
    $artifactBase = Require-EnvironmentValue -Name "DIVAN_UPDATER_ARTIFACT_BASE_URL"
    $signCommandTemplate = Require-EnvironmentValue -Name "DIVAN_WINDOWS_SIGN_COMMAND"
    $privateKey = Require-EnvironmentValue -Name "TAURI_SIGNING_PRIVATE_KEY"

    Assert-HttpsUrl -Name "DIVAN_UPDATER_ENDPOINT" -Value $updaterEndpoint | Out-Null
    Assert-HttpsUrl -Name "DIVAN_UPDATER_ARTIFACT_BASE_URL" -Value $artifactBase | Out-Null

    python (Join-Path $repoRoot "scripts/prepare_desktop_release_config.py") --root $repoRoot --output $configPath | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $configPath -PathType Leaf)) {
        throw "Production Tauri release configuration validation failed"
    }

    $version = (Get-Content (Join-Path $tauriRoot "tauri.conf.json") -Raw | ConvertFrom-Json).version
    if ($version -notmatch '^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$') {
        throw "Desktop version is not SemVer-compatible"
    }
    if (-not $env:GITHUB_REPOSITORY -or $env:GITHUB_REPOSITORY -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$') {
        throw "GITHUB_REPOSITORY is required for production artifact identity"
    }
    $tag = "desktop-v$version"
    $expectedArtifactBase = "https://github.com/$env:GITHUB_REPOSITORY/releases/download/$tag"
    if ($artifactBase.TrimEnd('/') -ne $expectedArtifactBase) {
        throw "DIVAN_UPDATER_ARTIFACT_BASE_URL must target the exact immutable Desktop release tag $tag"
    }

    if ($signCommandTemplate -notlike '*%1*') {
        throw "DIVAN_WINDOWS_SIGN_COMMAND must contain Tauri's %1 file placeholder"
    }
    $systemProbe = Join-Path $env:SystemRoot "System32/where.exe"
    if (-not (Test-Path $systemProbe -PathType Leaf)) {
        throw "Windows Authenticode probe executable was not found"
    }
    Copy-Item $systemProbe $authenticodeProbe -Force
    $quotedProbe = '"' + $authenticodeProbe + '"'
    $signCommand = $signCommandTemplate.Replace("%1", $quotedProbe)
    if ($signCommand -like '*%1*') {
        throw "Windows sign command placeholder was not fully resolved"
    }
    & $env:ComSpec /d /s /c $signCommand | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Production Authenticode sign command failed on the isolated probe executable"
    }

    $authenticode = Get-AuthenticodeSignature $authenticodeProbe
    if ($authenticode.Status -ne "Valid" -or -not $authenticode.SignerCertificate) {
        throw "Production Authenticode probe signature is not valid: $($authenticode.Status)"
    }
    $now = [DateTime]::UtcNow
    if ($authenticode.SignerCertificate.NotBefore.ToUniversalTime() -gt $now) {
        throw "Production Authenticode signer certificate is not valid yet"
    }
    if ($authenticode.SignerCertificate.NotAfter.ToUniversalTime() -le $now) {
        throw "Production Authenticode signer certificate is expired"
    }
    $signerThumbprintHash = Get-Sha256Text -Value $authenticode.SignerCertificate.Thumbprint

    [IO.File]::WriteAllBytes($updaterProbe, [Text.Encoding]::UTF8.GetBytes("Ottoman production updater signing readiness probe`n"))
    Push-Location $desktopRoot
    try {
        $signerOutput = & pnpm tauri signer sign $updaterProbe 2>&1
        $signerExit = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
    if ($signerExit -ne 0) {
        throw "Production Tauri updater private key could not sign the readiness probe"
    }
    $signerText = ($signerOutput | Out-String).Trim()
    if (-not $signerText) {
        throw "Tauri signer returned no signature output for the readiness probe"
    }

    $evidence = [ordered]@{
        schema_version = 1
        status = "pass"
        product = "Ottoman Desktop"
        source_commit = $sourceCommit
        source_tree = $sourceTree
        version = $version
        production_environment = "production-release"
        release_overlay_valid = $true
        updater_public_key_configured = $true
        updater_public_key_sha256 = Get-Sha256Text -Value $publicKey.Trim()
        updater_endpoint_https = $true
        artifact_base_exact_release_tag = $true
        authenticode_sign_command_usable = $true
        authenticode_signature_valid = $true
        authenticode_signer_thumbprint_sha256 = $signerThumbprintHash
        authenticode_certificate_not_after_utc = $authenticode.SignerCertificate.NotAfter.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        tauri_private_key_sign_probe = $true
        tauri_private_key_password_configured = [bool]($env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD)
        private_signing_material_persisted = $false
        secret_values_in_evidence = $false
    }

    $outputParent = Split-Path -Parent $Output
    if ($outputParent) {
        New-Item -ItemType Directory -Path $outputParent -Force | Out-Null
    }
    $evidence | ConvertTo-Json -Depth 8 | Set-Content -Path $Output -Encoding utf8
}
finally {
    Remove-Item $testRoot -Recurse -Force -ErrorAction SilentlyContinue
}
