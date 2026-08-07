param(
    [Parameter(Mandatory = $true)]
    [string]$Output,

    [Parameter(Mandatory = $true)]
    [string]$Transcript
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$transcriptParent = Split-Path -Parent $Transcript
if ($transcriptParent) {
    New-Item -ItemType Directory -Path $transcriptParent -Force | Out-Null
}
Remove-Item $Transcript -Force -ErrorAction SilentlyContinue

$failure = $null
Start-Transcript -Path $Transcript -Force | Out-Null
try {
    & "$PSScriptRoot/windows_desktop_updater_e2e.ps1" -Output $Output
    if ($LASTEXITCODE -ne 0) {
        throw "updater e2e child exited with code $LASTEXITCODE"
    }
}
catch {
    $failure = $_
}
finally {
    try {
        Stop-Transcript | Out-Null
    }
    catch {
        # Keep the original updater failure authoritative.
    }
}

if ($null -ne $failure) {
    $message = [string]$failure.Exception.Message
    $escaped = $message.Replace("%", "%25").Replace("`r", "%0D").Replace("`n", "%0A")
    Write-Host "::error title=Signed updater E2E::$escaped"

    if (Test-Path $Transcript -PathType Leaf) {
        $tail = @(Get-Content $Transcript -Tail 120)
        foreach ($line in $tail) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                $safe = $line.Replace("%", "%25").Replace("`r", "%0D").Replace("`n", "%0A")
                Write-Host "::notice title=Updater E2E trace::$safe"
            }
        }
    }
    throw $failure
}

if (-not (Test-Path $Output -PathType Leaf)) {
    throw "updater e2e completed without evidence output"
}
